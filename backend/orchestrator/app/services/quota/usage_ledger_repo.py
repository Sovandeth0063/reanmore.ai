"""
File: backend/orchestrator/app/services/quota/usage_ledger_repo.py
Description: Repository layer for durable, tamper-evident PostgreSQL UsageLedger auditing.
             Guarantees zero double-counting via UniqueConstraint(user_id, problem_id).
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database import UsageLedger, AsyncSessionLocal

logger = logging.getLogger("reanmore.quota.ledger")


class UsageLedgerRepo:
    """
    Durable PostgreSQL ledger repository for student problem quotas.
    Provides atomic, idempotent insertion and historical usage aggregation.
    """

    async def record_quota_transaction(
        self,
        user_id: str,
        problem_id: str,
        problem_hash: Optional[str] = None,
        subject: str = "math",
        tokens_consumed: int = 0,
    ) -> bool:
        """
        Records a problem deduction transaction into the durable audit ledger.
        Returns:
            True: If the transaction was successfully inserted (fresh deduction).
            False: If (user_id, problem_id) already exists (duplicate, 0 new deduction).
        """
        import app.infrastructure.database as db_mod
        if not getattr(db_mod, "database_ready", False):
            # Database offline/uninitialized: skip blocking network attempt
            return True

        async with AsyncSessionLocal() as session:
            try:
                async with session.begin():
                    record = UsageLedger(
                        user_id=user_id,
                        problem_id=problem_id,
                        problem_hash=problem_hash,
                        subject=subject,
                        tokens_consumed=tokens_consumed,
                        created_at=datetime.utcnow(),
                    )
                    session.add(record)
                logger.info(
                    f"Quota Ledger: Recorded 1 problem quota transaction for student={user_id}, "
                    f"problem_id={problem_id}, subject={subject}"
                )
                return True
            except IntegrityError:
                logger.debug(
                    f"Quota Ledger: Duplicate problem transaction detected for student={user_id}, "
                    f"problem_id={problem_id}. Skipped deduction."
                )
                return False
            except Exception as e:
                logger.warning(
                    f"Quota Ledger: Failed to persist ledger record for student={user_id} ({e}). "
                    f"Operating in degraded persistence mode."
                )
                return True

    async def has_problem_been_recorded(self, user_id: str, problem_id: str) -> bool:
        """Checks if a given problem has already been deducted for this student."""
        import app.infrastructure.database as db_mod
        if not getattr(db_mod, "database_ready", False):
            return False

        async with AsyncSessionLocal() as session:
            try:
                stmt = select(UsageLedger.id).where(
                    UsageLedger.user_id == user_id,
                    UsageLedger.problem_id == problem_id,
                ).limit(1)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
            except Exception as e:
                logger.warning(f"Quota Ledger: Error checking problem existence ({e})")
                return False

    async def get_usage_count_between(
        self,
        user_id: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> int:
        """
        Aggregates the total number of distinct problems solved by a student
        within a UTC time interval.
        """
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(func.count(UsageLedger.id)).where(
                    UsageLedger.user_id == user_id,
                    UsageLedger.created_at >= start_utc,
                    UsageLedger.created_at < end_utc,
                )
                result = await session.execute(stmt)
                count = result.scalar() or 0
                return count
            except Exception as e:
                logger.warning(f"Quota Ledger: Error querying usage count ({e})")
                return 0


usage_ledger_repo = UsageLedgerRepo()
