"""
File: testing/test_pipeline_trace.py
Description: Tests for Orchestrator Question Projection Pipeline Trace.
             Verifies:
             1. Raw Query -> Normalize (math standardization, kid slang, units)
             2. Rewrite if needed (pronouns, active step context, self-contained check)
             3. Route to Microservice (MATH_SERVICE, SCIENCE_SERVICE, ORCHESTRATOR_GUARDRAILS)
             4. Result summarization and tidy log box formatting
             5. Integration with /api/query endpoint payload
"""

import os
import sys

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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator")))

from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from app.main import app
# pyrefly: ignore [missing-import]
from app.services.pipeline_tracer import (
    PipelineTrace,
    normalize_query,
    resolve_query_rewrite,
    determine_routing,
    format_tidy_pipeline_log,
)

client = TestClient(app)


def test_normalize_query():
    # Test fraction standardization
    assert normalize_query("½ + ¼") == "1/2 + 1/4"
    # Test exponent
    assert "^" in normalize_query("x²") or "**" in normalize_query("x²") or "2" in normalize_query("x²")
    # Test unit spacing
    assert "10 cm" in normalize_query("10cm")
    # Test kid typos
    assert "photo" in normalize_query("wat is photosynthesiss").lower()


def test_resolve_query_rewrite_self_contained():
    q = "What is 15 - 7?"
    rewritten, needed, note = resolve_query_rewrite(
        query=q,
        normalized_query=q,
        active_step=None,
        previous_query=None,
        has_active_problem=False
    )
    assert needed is False
    assert rewritten == q
    assert "Self-contained" in note


def test_resolve_query_rewrite_with_active_step_pronoun():
    active_step = {
        "step_number": 1,
        "title": "Count the apples",
        "mission": "Find out how many apples are left after giving 3 away."
    }
    q = "how do i solve it?"
    rewritten, needed, note = resolve_query_rewrite(
        query=q,
        normalized_query=q,
        active_step=active_step,
        previous_query="I have 10 apples and give 3 away",
        has_active_problem=True
    )
    assert needed is True
    assert "apples" in rewritten.lower() or "step 1" in rewritten.lower()
    assert rewritten.lower() != q.lower()


def test_resolve_query_rewrite_with_bare_answer_attempt():
    active_step = {
        "step_number": 2,
        "title": "Calculate difference",
        "mission": "Subtract 3 from 10."
    }
    q = "7"
    rewritten, needed, note = resolve_query_rewrite(
        query=q,
        normalized_query=q,
        active_step=active_step,
        previous_query=None,
        has_active_problem=True
    )
    assert needed is True
    assert "Step 2 Attempt: '7'" in rewritten


def test_determine_routing():
    # Math routing
    target, ep, reason = determine_routing(
        subject="MATH",
        subtopic="word_problem",
        intent="INITIAL_QUESTION",
        is_deflected=False,
        is_safe=True
    )
    assert target == "IN_PROCESS_MATH_CAS"
    assert "cas" in ep

    # Science routing
    target, ep, reason = determine_routing(
        subject="SCIENCE",
        subtopic="plants_biology",
        intent="INITIAL_QUESTION",
        is_deflected=False,
        is_safe=True
    )
    assert target == "SCIENCE_SERVICE"
    assert "/solve" in ep

    # Guardrails deflection
    target, ep, reason = determine_routing(
        subject="GENERAL",
        subtopic="gaming",
        intent="OFF_TOPIC_DEFLECTED",
        is_deflected=True,
        is_safe=True
    )
    assert target == "ORCHESTRATOR_GUARDRAILS"


def test_format_tidy_pipeline_log():
    trace = PipelineTrace(
        session_id="test_sess_42",
        grade_level="grade_1_3",
        raw_query="3x+5=20",
        normalized_query="3*x + 5 = 20",
        rewrite_needed=False,
        rewritten_query="3*x + 5 = 20",
        rewrite_note="Self-contained query",
        subject="MATH",
        subtopic="algebra",
        intent="INITIAL_QUESTION",
        target_service="MATH_SERVICE",
        service_endpoint="http://localhost:8001/solve",
        routing_reason="Algebra equation decomposition",
        result_summary="Created 3 Socratic steps | Active: Step 1",
        is_deflected=False,
        is_problem_complete=False,
        latency_ms=25.40,
        status="SUCCESS"
    )
    box = format_tidy_pipeline_log(trace)
    assert "[QUESTION PIPELINE PROJECTION TRACE]" in box
    assert "1. Raw Query" in box
    assert "2. Normalize" in box
    assert "3. Rewrite" in box
    assert "4. Routing" in box
    assert "5. Results" in box
    assert "MATH_SERVICE" in box
    assert "25.40 ms" in box


def test_api_query_returns_pipeline_trace():
    payload = {
        "query": "If Lily has 10 marbles and gives 4 to Sam, how many marbles does Lily have left?",
        "session_id": "test_pipeline_trace_session",
        "grade_level": "grade_1_3",
        "language": "en"
    }
    res = client.post("/api/query", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "pipeline_trace" in data
    trace = data["pipeline_trace"]
    assert trace is not None
    assert trace["raw_query"] == payload["query"]
    assert "marbles" in trace["normalized_query"]
    assert trace["subject"] == "math" or trace["subject"] == "MATH"
    assert "target_service" in trace
    assert "result_summary" in trace
    assert trace["latency_ms"] >= 0.0
