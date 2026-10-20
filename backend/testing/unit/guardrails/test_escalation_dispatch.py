"""
File: backend/testing/unit/guardrails/test_escalation_dispatch.py
Description: Exhaustive test suite for Crisis Escalation Protocol & Live Dispatcher (Phase 5).
             - Verifies content-free notification ping invariant (Zero child PII or raw text).
             - Verifies Counselor/Safeguarding Lead first routing (never parent directly).
             - Verifies external webhook dispatch, network fault tolerance, and honest degradation.
             - Verifies auto-escalation to Principal/Backup after 15-minute SLA breach.
             - Verifies end-to-end integration with LangGraph guardrails node.
"""

import os
import sys
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

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

# pyrefly: ignore [missing-import]
from app.core.tutoring_config import (
    CHILD_HELPLINE_CAMBODIA,
    EMERGENCY_AMBULANCE_CAMBODIA,
    SAFEGUARDING_REVIEW_SLA_MINUTES,
    DEFAULT_SAFEGUARDING_OWNER,
    SAFEGUARDING_PORTAL_URL,
)
# pyrefly: ignore [missing-import]
from app.services.guardrails.escalation import (
    format_content_free_notification_ping,
    dispatch_safety_alert,
    dispatch_escalation_alert,
    dispatch_external_safeguarding_ping,
    get_safeguarding_review_queue,
    clear_safeguarding_review_queue,
    acknowledge_safeguarding_alert,
    check_and_escalate_unacknowledged,
    SafeguardingAlertRecord,
)
# pyrefly: ignore [missing-import]
from app.services.guardrails.safety_filter import SafetyFilter, SafetyResult, SafetyCategory
# pyrefly: ignore [missing-import]
from app.services.socratic.graph import build_socratic_graph
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture(autouse=True)
def clean_review_queue():
    clear_safeguarding_review_queue()
    yield
    clear_safeguarding_review_queue()


def test_content_free_notification_ping_invariant():
    """Verify notification ping is strictly content-free: token and portal URL only."""
    token = "STU-9876ABCD"
    ping = format_content_free_notification_ping(token, sla_minutes=15)

    # Must contain token, SLA, portal URL
    assert token in ping
    assert "15m" in ping
    assert SAFEGUARDING_PORTAL_URL in ping

    # STRICT INVARIANT: Zero child PII, quotes, or keywords
    assert "student" not in ping.lower()
    assert "problem" not in ping.lower()
    assert "score" not in ping.lower()
    assert '"' not in ping
    assert "'" not in ping


def test_tier2_abuse_routes_to_safeguarding_lead_never_parent():
    """Verify child abuse disclosures route to School Safeguarding Lead first."""
    decision = dispatch_safety_alert(
        session_id="sess_abuse_01",
        severity_tier=2,
        category="TIER2_CHILD_ABUSE",
        text_snippet="My uncle hurts me",
        student_token="STU-ABUSE-01",
    )

    assert decision["escalated"] is True
    assert decision["channel"] == "school_safeguarding_lead"
    assert decision["target_recipient"] == "SCHOOL_SAFEGUARDING_LEAD"
    assert decision["tutor_state"] == "PAUSED"
    assert CHILD_HELPLINE_CAMBODIA in decision["child_facing_guidance"]

    # Verify queue record
    q = get_safeguarding_review_queue()
    assert len(q) == 1
    assert q[0].owner == DEFAULT_SAFEGUARDING_OWNER
    assert q[0].student_token == "STU-ABUSE-01"


def test_tier2_self_harm_routes_to_counselor():
    """Verify self-harm signals route to School Counselor first."""
    decision = dispatch_safety_alert(
        session_id="sess_harm_01",
        severity_tier=2,
        category="TIER2_SELF_HARM",
        text_snippet="I want to die",
        student_token="STU-HARM-01",
    )

    assert decision["escalated"] is True
    assert decision["channel"] == "school_counselor"
    assert decision["target_recipient"] == "SCHOOL_COUNSELOR"
    assert decision["tutor_state"] == "PAUSED"
    assert CHILD_HELPLINE_CAMBODIA in decision["child_facing_guidance"]
    assert EMERGENCY_AMBULANCE_CAMBODIA in decision["child_facing_guidance"]


def test_recusal_conflict_routes_to_district_focal_point():
    """Verify conflict-of-interest recusal bypasses school staff to District Focal Point."""
    decision = dispatch_safety_alert(
        session_id="sess_recusal_01",
        severity_tier=2,
        category="TIER2_CHILD_ABUSE",
        has_recusal_conflict=True,
        student_token="STU-RECUSAL-01",
    )

    assert decision["target_recipient"] == "DISTRICT_SAFEGUARDING_FOCAL_POINT"
    assert decision["channel"] == "district_safeguarding_focal_point"
    assert decision["action"] == "DISPATCH_DISTRICT_RECUSAL_ALERT"


def test_unconfigured_webhook_logs_and_skips():
    """When webhook is unconfigured, alert is queued and logged without error."""
    with patch("app.core.config.settings.SAFEGUARDING_WEBHOOK_URL", ""):
        decision = dispatch_safety_alert(
            session_id="sess_nowebhook",
            severity_tier=2,
            category="TIER2_IMMEDIATE_DANGER",
            student_token="STU-NOWEBHOOK",
        )

        assert decision["dispatch_status"] == "SKIPPED_NO_WEBHOOK"
        assert decision["dispatch_channel"] == "log"


def test_external_webhook_dispatch_success():
    """Verify successful HTTP POST of content-free ping to external webhook."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.post", return_value=mock_resp) as mock_post:
        decision = dispatch_safety_alert(
            session_id="sess_webhook_ok",
            severity_tier=2,
            category="TIER2_CHILD_ABUSE",
            student_token="STU-HOOK-OK",
            webhook_url="https://external.safeguarding.edu.kh/alerts",
        )

        assert decision["dispatch_status"] == "DISPATCHED"
        assert decision["dispatch_channel"] == "webhook"
        assert mock_post.called

        # Verify posted payload
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "https://external.safeguarding.edu.kh/alerts"
        payload = call_kwargs["json"]

        assert payload["student_token"] == "STU-HOOK-OK"
        assert payload["event"] == "safeguarding_review_pending"
        assert payload["portal_url"] == SAFEGUARDING_PORTAL_URL
        assert payload["severity_tier"] == 2
        # INVARIANT: Zero child message text in external payload
        assert "text" not in payload
        assert "message" not in payload
        assert "child" not in payload


def test_external_webhook_dispatch_http_error_honest_degradation():
    """Verify HTTP 500 from webhook fails gracefully without throwing an unhandled error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 502
    mock_resp.text = "Bad Gateway"

    with patch("httpx.post", return_value=mock_resp):
        decision = dispatch_safety_alert(
            session_id="sess_webhook_fail",
            severity_tier=2,
            category="TIER2_SELF_HARM",
            student_token="STU-HOOK-502",
            webhook_url="https://external.safeguarding.edu.kh/alerts",
        )

        # Honest degradation: status is FAILED, error captured, session PAUSED
        assert decision["dispatch_status"] == "FAILED"
        assert "HTTP 502" in decision["dispatch_result"]["error"]
        assert decision["tutor_state"] == "PAUSED"


def test_external_webhook_dispatch_network_timeout_honest_degradation():
    """Verify network exception from webhook fails gracefully without crashing tutor turn."""
    import httpx

    with patch("httpx.post", side_effect=httpx.ConnectTimeout("Connection timed out")):
        decision = dispatch_safety_alert(
            session_id="sess_webhook_timeout",
            severity_tier=2,
            category="TIER2_CHILD_ABUSE",
            student_token="STU-HOOK-TIMEOUT",
            webhook_url="https://external.safeguarding.edu.kh/alerts",
        )

        assert decision["dispatch_status"] == "FAILED"
        assert "Connection timed out" in decision["dispatch_result"]["error"]


def test_check_and_escalate_unacknowledged_alerts_after_15m():
    """Verify unacknowledged alerts auto-escalate from level 1 to level 2 after SLA."""
    # Dispatch an alert
    dispatch_safety_alert(
        session_id="sess_sla_test",
        severity_tier=2,
        category="TIER2_CHILD_ABUSE",
        student_token="STU-SLA-TEST",
    )
    q = get_safeguarding_review_queue()
    assert len(q) == 1
    assert q[0].escalation_level == 1
    assert q[0].status == "PENDING_REVIEW"

    # Simulate 16 minutes passing during school hours
    alert_time = datetime.fromisoformat(q[0].created_at_utc)
    future_time = alert_time + timedelta(minutes=16)

    escalated = check_and_escalate_unacknowledged(current_time_utc=future_time)
    assert len(escalated) == 1
    assert escalated[0].escalation_level == 2
    assert escalated[0].target_recipient == "SCHOOL_PRINCIPAL_BACKUP"
    assert escalated[0].status == "AUTO_ESCALATED"


def test_acknowledge_safeguarding_alert():
    """Verify safeguarding lead can acknowledge an open alert."""
    dispatch_safety_alert(
        session_id="sess_ack_test",
        severity_tier=2,
        category="TIER2_SELF_HARM",
        student_token="STU-ACK-TEST",
    )
    q = get_safeguarding_review_queue()
    event_id = q[0].event_id

    ack_success = acknowledge_safeguarding_alert(event_id, acknowledged_by="Counselor_Kosal")
    assert ack_success is True

    updated_q = get_safeguarding_review_queue()
    assert updated_q[0].status == "ACKNOWLEDGED"
    assert updated_q[0].acknowledged_by == "Counselor_Kosal"


def test_graph_tier2_crisis_triggers_escalation_alert():
    """Verify that end-to-end LangGraph halts and dispatches crisis alert on Tier 2 input."""
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_graph_crisis_escalation"}}

    state = {
        "raw_user_input": "My dad hits me every day and I am afraid to go home",
        "session_id": "test_graph_crisis_escalation",
    }

    result = graph.invoke(state, config=config)

    # Graph must halt
    assert result["is_safe"] is False
    assert result["is_deflected"] is True

    # Review queue must have recorded the safeguarding alert
    q = get_safeguarding_review_queue()
    assert len(q) >= 1
    matching = [r for r in q if r.session_id == "test_graph_crisis_escalation"]
    assert len(matching) == 1
    assert matching[0].target_recipient == "SCHOOL_SAFEGUARDING_LEAD"
    assert matching[0].severity_tier == 2
