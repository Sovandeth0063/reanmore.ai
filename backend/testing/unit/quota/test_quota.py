"""
File: backend/testing/unit/quota/test_quota.py
Description: Unit and integration tests for Phase 3 Quota Subsystem.
             Enforces 10 problems/day and 300 problems/month per student,
             Asia/Phnom_Penh midnight resets, two-phase check/commit,
             teacher exemption, idempotency, and free Socratic interactions.
"""

# pyrefly: ignore [missing-import]
import os
import sys
import pytest
from datetime import datetime
import zoneinfo
from httpx import AsyncClient, ASGITransport

# Ensure repo root and orchestrator are on sys.path
def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "orchestrator")))

# pyrefly: ignore [missing-import]
from app.main import app
# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.services.quota.quota_guard import (
    quota_guard,
    QuotaGuard,
    QuotaCheckResult,
    QuotaExhaustedException,
)
# pyrefly: ignore [missing-import]
from app.services.auth.security import create_access_token


@pytest.fixture(autouse=True)
def reset_quota_state():
    """Reset local quota counters before each test run."""
    quota_guard.reset_local_state()
    yield
    quota_guard.reset_local_state()


# ── 1. Timezone & TTL Calculation Tests ──

def test_phnom_penh_timezone_and_ttl():
    guard = QuotaGuard(connect_redis=False)
    now = guard.get_phnom_penh_now()

    # Timezone must be UTC+7 Asia/Phnom_Penh
    assert now.tzinfo is not None
    assert "Phnom_Penh" in str(now.tzinfo)

    ttl = guard.get_seconds_until_midnight(now)
    assert 1 <= ttl <= 86400

    month_ttl = guard.get_seconds_until_month_end(now)
    assert month_ttl >= ttl


# ── 2. Quota Check & 10 Problems/Day Limit Tests ──

@pytest.mark.asyncio
async def test_quota_check_allows_fresh_student():
    student_id = "test_student_fresh_01"
    res = await quota_guard.check_quota(user_id=student_id, role="student")

    assert res.allowed is True
    assert res.daily_used == 0
    assert res.daily_remaining == 10
    assert res.monthly_remaining == 300
    assert res.is_exempt is False


@pytest.mark.asyncio
async def test_quota_10_problems_cutoff_and_11th_rejected():
    student_id = "test_student_ten_cap"

    # Commit 10 distinct problems sequentially
    for i in range(1, 11):
        check = await quota_guard.check_quota(user_id=student_id, role="student", problem_id=f"prob_{i}")
        assert check.allowed is True
        commit = await quota_guard.commit_quota(
            user_id=student_id,
            problem_id=f"prob_{i}",
            subject="math",
        )
        assert commit.committed is True
        assert commit.daily_used == i
        assert commit.daily_remaining == (10 - i)

    # 11th problem check must be strictly REJECTED
    check_11 = await quota_guard.check_quota(user_id=student_id, role="student", problem_id="prob_11")
    assert check_11.allowed is False
    assert check_11.daily_used == 10
    assert check_11.daily_remaining == 0
    assert check_11.error_km is not None
    assert "១០/ថ្ងៃ" in check_11.error_km
    assert "10 problems for today" in check_11.error_en

    # Raising exception must create standard HTTP 429 with Retry-After header
    exc = QuotaExhaustedException(check_11)
    assert exc.status_code == 429
    assert "Retry-After" in exc.headers
    assert exc.detail["error"] == "QUOTA_EXHAUSTED"


# ── 3. Teacher and Admin Exemption Tests ──

@pytest.mark.asyncio
async def test_teacher_and_admin_exempt():
    teacher_id = "test_teacher_hero"

    # Teachers can submit unlimited problems
    for i in range(1, 15):
        check = await quota_guard.check_quota(user_id=teacher_id, role="teacher")
        assert check.allowed is True
        assert check.is_exempt is True
        commit = await quota_guard.commit_quota(user_id=teacher_id, problem_id=f"prob_{i}", role="teacher")
        assert commit.committed is False  # 0 deduction recorded

    admin_id = "test_admin_boss"
    admin_check = await quota_guard.check_quota(user_id=admin_id, role="admin")
    assert admin_check.allowed is True
    assert admin_check.is_exempt is True


# ── 4. Zero Double-Counting & Idempotency Tests ──

@pytest.mark.asyncio
async def test_zero_double_counting_on_same_problem():
    student_id = "test_student_idempotency"
    problem_id = "math_fractions_ex_4"

    # First attempt: commits 1 quota point
    commit_1 = await quota_guard.commit_quota(user_id=student_id, problem_id=problem_id, subject="math")
    assert commit_1.committed is True
    assert commit_1.daily_used == 1

    # Second submission of same problem: must be recognized as duplicate (0 quota deducted)
    check_2 = await quota_guard.check_quota(user_id=student_id, problem_id=problem_id)
    assert check_2.allowed is True
    assert check_2.is_duplicate is True

    commit_2 = await quota_guard.commit_quota(user_id=student_id, problem_id=problem_id, subject="math")
    assert commit_2.committed is False
    assert commit_2.duplicate is True
    assert commit_2.daily_used == 1  # Still 1, NOT 2!


# ── 5. Free Socratic Actions Invariant ──

@pytest.mark.asyncio
async def test_step_validate_and_hints_consume_zero_quota():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step validation endpoint call
        val_res = await client.post(
            "/api/step/validate",
            json={
                "student_answer": "12",
                "expected_answer": "12",
                "step_number": 1,
                "language": "km",
            },
        )
        assert val_res.status_code == 200
        assert val_res.json()["is_correct"] is True

        # Check that no quota counters were touched
        assert len(quota_guard._local_counters) == 0


# ── 6. Two-Phase Rollback on Failure ──

@pytest.mark.asyncio
async def test_two_phase_rollback_preserves_quota_on_failure():
    student_id = "test_student_rollback"
    problem_id = "broken_problem_01"

    # Phase 1: Check passes
    check = await quota_guard.check_quota(user_id=student_id, problem_id=problem_id)
    assert check.allowed is True

    # Simulated solver crash: commit_quota is NEVER called!
    # Quota remains 0 used, 10 remaining
    day_str, month_str = quota_guard.get_date_keys()
    d_used, _ = quota_guard._get_current_usage(student_id, day_str, month_str)
    assert d_used == 0


# ── 7. End-to-End API Integration & HTTP 429 Verification ──

@pytest.mark.asyncio
async def test_query_endpoint_returns_429_when_quota_exhausted():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create student JWT token
        token_payload = {
            "sub": "student_capped_e2e",
            "user_id": "student_capped_e2e",
            "student_name": "somnang",
            "role": "student",
            "class_code": "GRADE4A",
            "grade_level": 4,
        }
        token = create_access_token(token_payload, settings.AUTH_SECRET_KEY, expires_in_seconds=3600)
        auth_header = {"Authorization": f"Bearer {token}"}

        # Simulate 10 problems already used today
        now = quota_guard.get_phnom_penh_now()
        day_str, month_str = quota_guard.get_date_keys(now)
        daily_key = quota_guard._get_daily_key("student_capped_e2e", day_str)
        quota_guard._local_counters[daily_key] = 10

        # Attempt to create an 11th new problem plan
        query_res = await client.post(
            "/api/query",
            json={
                "query": "Solve 15 + 25 step by step",
                "grade_level": "grade_4_6",
                "language": "en",
            },
            headers=auth_header,
        )

        assert query_res.status_code == 429
        data = query_res.json()
        assert data["detail"]["error"] == "QUOTA_EXHAUSTED"
        assert "10 problems for today" in data["detail"]["message_eng"]
        assert data["detail"]["quota_remaining"]["daily"] == 0
        assert "Retry-After" in query_res.headers
