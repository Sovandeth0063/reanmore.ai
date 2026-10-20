"""
File: backend/orchestrator/app/services/quota/quota_guard.py
Description: Socratic Problem Quota Guard & Metering Engine.
             Enforces 10 problems/day and 300 problems/month per student with
             Phnom Penh midnight resets (Asia/Phnom_Penh, UTC+7), fast-path Redis
             counters, local in-memory fallback, and two-phase check/commit.
"""

from __future__ import annotations
import os
import json
import logging
from datetime import datetime, timedelta
import zoneinfo
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set, Tuple

import redis
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.quota.usage_ledger_repo import usage_ledger_repo

logger = logging.getLogger("reanmore.quota.guard")


@dataclass
class QuotaCheckResult:
    allowed: bool
    daily_used: int
    daily_limit: int
    daily_remaining: int
    monthly_used: int
    monthly_limit: int
    monthly_remaining: int
    reset_countdown_seconds: int
    reset_time_str: str
    is_exempt: bool = False
    is_duplicate: bool = False
    error_km: Optional[str] = None
    error_en: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "daily": {
                "used": self.daily_used,
                "limit": self.daily_limit,
                "remaining": self.daily_remaining,
            },
            "monthly": {
                "used": self.monthly_used,
                "limit": self.monthly_limit,
                "remaining": self.monthly_remaining,
            },
            "reset_countdown_seconds": self.reset_countdown_seconds,
            "reset_time_str": self.reset_time_str,
            "is_exempt": self.is_exempt,
            "is_duplicate": self.is_duplicate,
            "error_km": self.error_km,
            "error_en": self.error_en,
        }


@dataclass
class QuotaCommitResult:
    committed: bool
    daily_used: int
    daily_remaining: int
    monthly_used: int
    monthly_remaining: int
    duplicate: bool = False


class QuotaExhaustedException(HTTPException):
    """
    HTTP 429 exception raised when a student reaches their daily or monthly quota cap.
    Returns encouraging, child-friendly bilingual guidance and exact reset timer.
    """
    def __init__(self, check_result: QuotaCheckResult):
        detail = {
            "error": "QUOTA_EXHAUSTED",
            "message_khmer": check_result.error_km or "អ្នកបានប្រើប្រាស់ចំនួនសំណួរកំណត់ប្រចាំថ្ងៃអស់ហើយ (១០/ថ្ងៃ)។",
            "message_eng": check_result.error_en or "You've completed your 10 problems for today! Great job practicing.",
            "quota_remaining": {
                "daily": check_result.daily_remaining,
                "monthly": check_result.monthly_remaining,
            },
            "quota_used": {
                "daily": check_result.daily_used,
                "monthly": check_result.monthly_used,
            },
            "reset_countdown_seconds": check_result.reset_countdown_seconds,
            "reset_time": check_result.reset_time_str,
        }
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(max(1, check_result.reset_countdown_seconds))},
        )


def get_phnom_penh_tz() -> Any:
    """Returns Asia/Phnom_Penh timezone with zero-dependency UTC+7 fallback for platforms without tzdata."""
    try:
        return zoneinfo.ZoneInfo(settings.QUOTA_TZ)
    except Exception:
        from datetime import timezone
        return timezone(timedelta(hours=7), name="Asia/Phnom_Penh")


class QuotaGuard:
    """
    Two-Phase Quota Enforcement Engine:
      1. check_quota(user_id, role, problem_id): Gatekeeper verifying remaining quota.
      2. commit_quota(user_id, problem_id, subject): Deducts exactly 1 problem quota upon plan success.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None, connect_redis: bool = True):
        self.tz = get_phnom_penh_tz()
        self.redis_client: Optional[redis.Redis] = redis_client
        self._local_counters: Dict[str, int] = {}
        self._local_seen_problems: Set[str] = set()

        if self.redis_client is None and connect_redis:
            redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_password = os.getenv("REDIS_PASSWORD") or None
            try:
                client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    decode_responses=True,
                    socket_timeout=0.5,
                    socket_connect_timeout=0.5,
                )
                client.ping()
                self.redis_client = client
                logger.info("QuotaGuard: Redis client connected successfully.")
            except Exception as e:
                logger.warning(f"QuotaGuard: Redis unavailable ({e}). Operating in local in-memory fallback.")

    def get_phnom_penh_now(self) -> datetime:
        """Returns the current datetime in Asia/Phnom_Penh (UTC+7)."""
        return datetime.now(self.tz)

    def get_date_keys(self, now: Optional[datetime] = None) -> Tuple[str, str]:
        """Returns (day_str, month_str) calibrated to Asia/Phnom_Penh."""
        current = now or self.get_phnom_penh_now()
        day_str = current.strftime("%Y-%m-%d")
        month_str = current.strftime("%Y-%m")
        return day_str, month_str

    def get_seconds_until_midnight(self, now: Optional[datetime] = None) -> int:
        """Calculates exact remaining seconds until 00:00:00 midnight in Asia/Phnom_Penh."""
        current = now or self.get_phnom_penh_now()
        midnight = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return max(1, int((midnight - current).total_seconds()))

    def get_seconds_until_month_end(self, now: Optional[datetime] = None) -> int:
        """Calculates exact remaining seconds until the 1st of the next month in Asia/Phnom_Penh."""
        current = now or self.get_phnom_penh_now()
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else (current.month + 1)
        month_end = datetime(year, month, 1, 0, 0, 0, tzinfo=self.tz)
        return max(1, int((month_end - current).total_seconds()))

    def _get_daily_key(self, user_id: str, day_str: str) -> str:
        return f"quota:{user_id}:day:{day_str}"

    def _get_monthly_key(self, user_id: str, month_str: str) -> str:
        return f"quota:{user_id}:month:{month_str}"

    def _get_seen_key(self, user_id: str) -> str:
        return f"quota:{user_id}:seen_problems"

    def is_problem_already_paid(self, user_id: str, problem_id: Optional[str]) -> bool:
        """Checks if problem_id was already paid/committed by this student."""
        if not problem_id:
            return False
        
        seen_token = f"{user_id}:{problem_id}"
        if seen_token in self._local_seen_problems:
            return True

        if self.redis_client:
            try:
                if self.redis_client.sismember(self._get_seen_key(user_id), problem_id):
                    return True
            except Exception as e:
                logger.debug(f"QuotaGuard: Redis seen check failed ({e})")

        return False

    async def check_quota(
        self,
        user_id: str,
        role: str = "student",
        problem_id: Optional[str] = None,
    ) -> QuotaCheckResult:
        """
        Phase 1: Check Quota Gatekeeper.
        Verifies if student has remaining daily and monthly allowances.
        Exempts teachers/admins and already-paid problems (0 deduction).
        """
        now = self.get_phnom_penh_now()
        day_str, month_str = self.get_date_keys(now)
        ttl_daily = self.get_seconds_until_midnight(now)
        reset_time_str = "12:00 យប់ (Midnight ICT)"

        # 1. Teachers and Admins are exempt from quota limits
        if role in ("teacher", "admin"):
            return QuotaCheckResult(
                allowed=True,
                daily_used=0,
                daily_limit=settings.QUOTA_DAILY,
                daily_remaining=settings.QUOTA_DAILY,
                monthly_used=0,
                monthly_limit=settings.QUOTA_MONTHLY,
                monthly_remaining=settings.QUOTA_MONTHLY,
                reset_countdown_seconds=ttl_daily,
                reset_time_str=reset_time_str,
                is_exempt=True,
            )

        # 2. Check if problem is already committed (Zero Double-Counting Invariant)
        if problem_id:
            if self.is_problem_already_paid(user_id, problem_id):
                return QuotaCheckResult(
                    allowed=True,
                    daily_used=0,
                    daily_limit=settings.QUOTA_DAILY,
                    daily_remaining=settings.QUOTA_DAILY,
                    monthly_used=0,
                    monthly_limit=settings.QUOTA_MONTHLY,
                    monthly_remaining=settings.QUOTA_MONTHLY,
                    reset_countdown_seconds=ttl_daily,
                    reset_time_str=reset_time_str,
                    is_duplicate=True,
                )
            # Cross-check Postgres persistent ledger
            try:
                if await usage_ledger_repo.has_problem_been_recorded(user_id, problem_id):
                    self._local_seen_problems.add(f"{user_id}:{problem_id}")
                    return QuotaCheckResult(
                        allowed=True,
                        daily_used=0,
                        daily_limit=settings.QUOTA_DAILY,
                        daily_remaining=settings.QUOTA_DAILY,
                        monthly_used=0,
                        monthly_limit=settings.QUOTA_MONTHLY,
                        monthly_remaining=settings.QUOTA_MONTHLY,
                        reset_countdown_seconds=ttl_daily,
                        reset_time_str=reset_time_str,
                        is_duplicate=True,
                    )
            except Exception as e:
                logger.debug(f"QuotaGuard: DB ledger check failed ({e})")

        # 3. Retrieve current usage from Redis or local fallback
        daily_used, monthly_used = self._get_current_usage(user_id, day_str, month_str)

        daily_rem = max(0, settings.QUOTA_DAILY - daily_used)
        monthly_rem = max(0, settings.QUOTA_MONTHLY - monthly_used)

        # 4. Check Daily Cap (10 problems / day)
        if daily_used >= settings.QUOTA_DAILY:
            logger.info(f"QuotaGuard: Daily quota exceeded for student={user_id} ({daily_used}/{settings.QUOTA_DAILY})")
            try:
                from app.services.telemetry.gap_recorder import log_gap_event
                log_gap_event(
                    gap_type="system",
                    gap_code="QUOTA_EXHAUSTED",
                    severity=1,
                    user_id=user_id,
                    details={"quota_type": "daily", "used": daily_used, "limit": settings.QUOTA_DAILY}
                )
            except Exception:
                pass
            return QuotaCheckResult(
                allowed=False,
                daily_used=daily_used,
                daily_limit=settings.QUOTA_DAILY,
                daily_remaining=0,
                monthly_used=monthly_used,
                monthly_limit=settings.QUOTA_MONTHLY,
                monthly_remaining=monthly_rem,
                reset_countdown_seconds=ttl_daily,
                reset_time_str=reset_time_str,
                error_km="អ្នកបានប្រើប្រាស់ចំនួនសំណួរកំណត់ប្រចាំថ្ងៃអស់ហើយ (១០/ថ្ងៃ)។ សូមត្រឡប់មកវិញនៅថ្ងៃស្អែកវេលាម៉ោង ១២:០០ យប់!",
                error_en="You've completed your 10 problems for today! Great job practicing. Your quota resets at midnight Phnom Penh time.",
            )

        # 5. Check Monthly Cap (300 problems / month)
        if monthly_used >= settings.QUOTA_MONTHLY:
            logger.info(f"QuotaGuard: Monthly quota exceeded for student={user_id} ({monthly_used}/{settings.QUOTA_MONTHLY})")
            ttl_month = self.get_seconds_until_month_end(now)
            return QuotaCheckResult(
                allowed=False,
                daily_used=daily_used,
                daily_limit=settings.QUOTA_DAILY,
                daily_remaining=daily_rem,
                monthly_used=monthly_used,
                monthly_limit=settings.QUOTA_MONTHLY,
                monthly_remaining=0,
                reset_countdown_seconds=ttl_month,
                reset_time_str="ថ្ងៃទី ១ ខែបន្ទាប់ (1st of next month)",
                error_km="អ្នកបានប្រើប្រាស់ចំនួនសំណួរកំណត់ប្រចាំខែអស់ហើយ (៣០០/ខែ)។ សូមត្រឡប់មកវិញនៅខែក្រោយ!",
                error_en="You've reached your monthly limit of 300 problems! Excellent learning journey this month. Your quota resets next month.",
            )

        return QuotaCheckResult(
            allowed=True,
            daily_used=daily_used,
            daily_limit=settings.QUOTA_DAILY,
            daily_remaining=daily_rem,
            monthly_used=monthly_used,
            monthly_limit=settings.QUOTA_MONTHLY,
            monthly_remaining=monthly_rem,
            reset_countdown_seconds=ttl_daily,
            reset_time_str=reset_time_str,
        )

    async def commit_quota(
        self,
        user_id: str,
        problem_id: str,
        problem_hash: Optional[str] = None,
        subject: str = "math",
        tokens_consumed: int = 0,
        role: str = "student",
    ) -> QuotaCommitResult:
        """
        Phase 2: Commit Quota.
        Atomically increments Redis fast-path counters and writes to PostgreSQL audit ledger.
        Guarantees single deduction per problem lifecycle.
        """
        now = self.get_phnom_penh_now()
        day_str, month_str = self.get_date_keys(now)

        # 1. Teachers/Admins do not spend quota
        if role in ("teacher", "admin"):
            return QuotaCommitResult(
                committed=False,
                daily_used=0,
                daily_remaining=settings.QUOTA_DAILY,
                monthly_used=0,
                monthly_remaining=settings.QUOTA_MONTHLY,
            )

        # 2. Prevent double-counting if problem already committed
        if self.is_problem_already_paid(user_id, problem_id):
            daily_used, monthly_used = self._get_current_usage(user_id, day_str, month_str)
            return QuotaCommitResult(
                committed=False,
                daily_used=daily_used,
                daily_remaining=max(0, settings.QUOTA_DAILY - daily_used),
                monthly_used=monthly_used,
                monthly_remaining=max(0, settings.QUOTA_MONTHLY - monthly_used),
                duplicate=True,
            )

        # 3. Deduct quota in Redis / local memory
        daily_used, monthly_used = self._increment_usage(user_id, day_str, month_str, problem_id)
        self._local_seen_problems.add(f"{user_id}:{problem_id}")

        # 4. Durable audit ledger in PostgreSQL (background safe)
        try:
            await usage_ledger_repo.record_quota_transaction(
                user_id=user_id,
                problem_id=problem_id,
                problem_hash=problem_hash,
                subject=subject,
                tokens_consumed=tokens_consumed,
            )
        except Exception as e:
            logger.warning(f"QuotaGuard: Failed to write ledger in commit ({e})")

        logger.info(
            f"QuotaGuard: Committed 1 quota point for student={user_id}. "
            f"Daily: {daily_used}/{settings.QUOTA_DAILY}, Monthly: {monthly_used}/{settings.QUOTA_MONTHLY}"
        )

        return QuotaCommitResult(
            committed=True,
            daily_used=daily_used,
            daily_remaining=max(0, settings.QUOTA_DAILY - daily_used),
            monthly_used=monthly_used,
            monthly_remaining=max(0, settings.QUOTA_MONTHLY - monthly_used),
        )

    def _get_current_usage(self, user_id: str, day_str: str, month_str: str) -> Tuple[int, int]:
        """Reads current usage counts from Redis or local in-memory fallback."""
        daily_key = self._get_daily_key(user_id, day_str)
        monthly_key = self._get_monthly_key(user_id, month_str)

        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.get(daily_key)
                pipe.get(monthly_key)
                res_d, res_m = pipe.execute()
                d_val = int(res_d) if res_d else 0
                m_val = int(res_m) if res_m else 0
                return d_val, m_val
            except Exception as e:
                logger.debug(f"QuotaGuard: Redis usage read error ({e}), reading local cache")

        d_val = self._local_counters.get(daily_key, 0)
        m_val = self._local_counters.get(monthly_key, 0)
        return d_val, m_val

    def _increment_usage(
        self, user_id: str, day_str: str, month_str: str, problem_id: str
    ) -> Tuple[int, int]:
        """Atomically increments daily & monthly usage counters and records problem ID."""
        daily_key = self._get_daily_key(user_id, day_str)
        monthly_key = self._get_monthly_key(user_id, month_str)
        seen_key = self._get_seen_key(user_id)
        ttl_daily = self.get_seconds_until_midnight()
        ttl_monthly = self.get_seconds_until_month_end()

        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(daily_key)
                pipe.expire(daily_key, ttl_daily)
                pipe.incr(monthly_key)
                pipe.expire(monthly_key, ttl_monthly)
                pipe.sadd(seen_key, problem_id)
                pipe.expire(seen_key, ttl_monthly)
                res = pipe.execute()
                return int(res[0]), int(res[2])
            except Exception as e:
                logger.warning(f"QuotaGuard: Redis increment failed ({e}), falling back to local memory")

        # Fallback local memory
        self._local_counters[daily_key] = self._local_counters.get(daily_key, 0) + 1
        self._local_counters[monthly_key] = self._local_counters.get(monthly_key, 0) + 1
        return self._local_counters[daily_key], self._local_counters[monthly_key]

    def reset_local_state(self):
        """Utility for test suites to clear in-memory counters."""
        self._local_counters.clear()
        self._local_seen_problems.clear()


quota_guard = QuotaGuard()
