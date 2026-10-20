"""
File: backend/testing/unit/test_gap_recorder.py
Description: Unit tests for Unified Gap Accounting (Phase 1D).
             Verifies:
             - Anonymized user hashing (COPPA compliance)
             - Recursive PII scrubbing in details
             - Priority score mathematical formula
             - Asynchronous & synchronous gap recording (content, learner, system)
             - GapEvent ORM model compatibility
             - Weekly admin digest generation
"""

import os
import sys
import math
import pytest
from datetime import datetime, timezone

# Ensure repo and orchestrator paths
def _setup_path():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "backend")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    backend_dir = os.path.join(cur, "backend")
    orch_dir = os.path.join(backend_dir, "orchestrator")
    for p in (cur, backend_dir, orch_dir):
        if p not in sys.path:
            sys.path.insert(0, p)

_setup_path()

from app.services.telemetry.gap_recorder import (
    compute_user_hash,
    sanitize_gap_details,
    calculate_priority_score,
    GapRecorder,
    record_gap_event,
    log_gap_event,
)
from app.infrastructure.database import GapEvent


def test_user_hash_anonymization():
    """Verifies user_id is hashed with salt and raw IDs are never preserved."""
    raw_id_1 = "student_sochea_123"
    raw_id_2 = "student_bopha_456"

    hash_1 = compute_user_hash(raw_id_1)
    hash_2 = compute_user_hash(raw_id_2)
    hash_anon = compute_user_hash(None)

    assert hash_1 != raw_id_1
    assert hash_2 != raw_id_2
    assert hash_1 != hash_2
    assert len(hash_1) == 32
    # Deterministic with same salt
    assert compute_user_hash(raw_id_1) == hash_1
    assert hash_anon != hash_1


def test_sanitize_gap_details_pii():
    """Verifies recursive scrubbing of student PII from gap details."""
    raw_details = {
        "raw_query": "My name is Sochea and my phone is 012345678, what is 15 + 27?",
        "student_attempt": "Call me at test@example.com",
        "nested": {
            "notes": "Student John at 098765432"
        },
        "shape": "two_digit_add"
    }

    clean = sanitize_gap_details(raw_details)
    assert "012345678" not in clean["raw_query"]
    assert "test@example.com" not in clean["student_attempt"]
    assert clean["shape"] == "two_digit_add"


def test_priority_score_formula():
    """
    Verifies priority formula:
    Priority = Severity * log2(1 + Occurrences) * (1 + 0.5 * Distinct Students)
    """
    # Case: sev=2, occ=7 (1+7=8, log2(8)=3), students=4 (1 + 0.5*4 = 3)
    # Expected: 2 * 3 * 3 = 18.0
    score = calculate_priority_score(severity=2, occurrences=7, distinct_students=4)
    assert score == 18.0

    # Case: sev=1, occ=3 (1+3=4, log2(4)=2), students=2 (1 + 0.5*2 = 2)
    # Expected: 1 * 2 * 2 = 4.0
    score2 = calculate_priority_score(severity=1, occurrences=3, distinct_students=2)
    assert score2 == 4.0

    # Case: sev=3 (critical), occ=15 (log2(16)=4), students=6 (1 + 3 = 4)
    # Expected: 3 * 4 * 4 = 48.0
    score3 = calculate_priority_score(severity=3, occurrences=15, distinct_students=6)
    assert score3 == 48.0


@pytest.mark.asyncio
async def test_record_gap_event_content():
    """Tests recording a content gap event."""
    recorder = GapRecorder(max_buffer_size=100)
    event = await recorder.record_gap_event(
        gap_type="content",
        gap_code="NO_SKILL_MATCH",
        severity="warning",
        user_id="student_khemarak",
        session_id="sess_test_101",
        grade_tier="grade_4_6",
        skill_id="fraction_divide",
        details={"shape": "fraction_division", "problem": "Divide 3/4 by 1/2"}
    )

    assert event["gap_type"] == "content"
    assert event["gap_code"] == "NO_SKILL_MATCH"
    assert event["severity"] == 2
    assert event["grade_tier"] == "grade_4_6"
    assert event["user_hash"] == compute_user_hash("student_khemarak")
    assert "fraction_divide" in event["fingerprint"]

    # Check buffer
    mem = recorder.get_memory_events()
    assert len(mem) == 1
    assert mem[0]["gap_code"] == "NO_SKILL_MATCH"


@pytest.mark.asyncio
async def test_record_gap_event_learner():
    """Tests recording a learner misconception event."""
    recorder = GapRecorder(max_buffer_size=100)
    event = await recorder.record_gap_event(
        gap_type="learner",
        gap_code="MISCONCEPTION_REGROUP",
        severity=2,
        user_id="student_dara",
        session_id="sess_test_102",
        grade_tier="grade_1_3",
        skill_id="add_2digit_regroup",
        step_index=1,
        details={"concept": "ones_column_regroup", "attempt": "13"}
    )

    assert event["gap_type"] == "learner"
    assert event["gap_code"] == "MISCONCEPTION_REGROUP"
    assert event["step_index"] == 1


@pytest.mark.asyncio
async def test_record_gap_event_system():
    """Tests recording a system event (e.g. LEAK_BLOCKED or LLM_TIMEOUT)."""
    recorder = GapRecorder(max_buffer_size=100)
    event = await recorder.record_gap_event(
        gap_type="system",
        gap_code="LEAK_BLOCKED",
        severity="critical",
        session_id="sess_test_103",
        details={"reason": "target_token_found_in_prose", "target": "42"}
    )

    assert event["gap_type"] == "system"
    assert event["gap_code"] == "LEAK_BLOCKED"
    assert event["severity"] == 3


def test_gap_event_orm_model():
    """Tests GapEvent ORM model instantiation and property aliases."""
    db_event = GapEvent(
        gap_type="content",
        gap_code="PARSE_UNCONFIRMED",
        severity=2,
        user_hash="hash123",
        session_id="sess_123",
        grade_tier="grade_1_3",
        subject="math",
        fingerprint="fp123",
        details={"query": "test query"},
    )

    assert db_event.event_code == "PARSE_UNCONFIRMED"
    assert db_event.grade_level == "grade_1_3"
    assert db_event.domain == "math"
    assert db_event.status == "open"
    assert db_event.resolved is False


def test_admin_digest_script_generation(tmp_path):
    """Verifies scripts/generate_admin_digest.py generates a valid markdown report."""
    from scripts.generate_admin_digest import (
        get_mock_digest_data,
        render_markdown_digest,
    )

    data = get_mock_digest_data(days=7)
    report_md = render_markdown_digest(data)

    assert "# ReanMore Weekly Admin & Pedagogical Audit Digest" in report_md
    assert "1. Executive Summary" in report_md
    assert "2. Top Content Gaps" in report_md
    assert "3. Top Learner Misconceptions" in report_md
    assert "4. System Reliability & Guardrails Audit" in report_md
    assert "Priority =" in report_md
    assert "LEAK_BLOCKED" in report_md
