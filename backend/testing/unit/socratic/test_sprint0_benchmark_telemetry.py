"""
File: backend/testing/unit/socratic/test_sprint0_benchmark_telemetry.py
Description: Unit test suite for Sprint 0:
             1. Benchmark Dataset (Task 0.1) - 500 items, splits, bilingual balance
             2. Safe Telemetry & Isolated Safety Audit Store (Task 0.2)
             3. Single-Threshold Ingress, Khmer Numerals, & UNCLEAR 3-Streak Degradation (Task 0.3)
"""

# pyrefly: ignore [missing-import]
import os
import sys
import json
import pytest

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

# pyrefly: ignore [missing-import]
from app.services.pipeline_tracer import PipelineTrace, format_tidy_pipeline_log
# pyrefly: ignore [missing-import]
from app.services.telemetry.safety_audit import (
    SafetyAuditStore,
    record_safety_event,
    get_safety_audit_store
)
# pyrefly: ignore [missing-import]
from app.services.socratic.intent_classifier import (
    classify_student_intent,
    classify_intent_node,
    INTENT_ANSWER_ATTEMPT,
    INTENT_UNCLEAR,
    INTENT_SAFETY,
    INTENT_ANSWER_DEMAND,
    INTENT_CLARIFICATION,
    INTENT_OFF_TOPIC,
    INGRESS_CONFIDENCE_THRESHOLD
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Benchmark Dataset Verification (Task 0.1)
# ─────────────────────────────────────────────────────────────────────────────

class TestBenchmarkCorpus:

    @pytest.fixture
    def benchmark_items(self):
        dataset_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "bilingual_intent_benchmark.jsonl"
        )
        assert os.path.exists(dataset_path), f"Benchmark file not found at {dataset_path}"
        items = []
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items

    def test_benchmark_total_size(self, benchmark_items):
        assert len(benchmark_items) == 500

    def test_benchmark_split_distribution(self, benchmark_items):
        dev_items = [x for x in benchmark_items if x.get("split") == "dev"]
        test_items = [x for x in benchmark_items if x.get("split") == "test"]
        assert len(dev_items) == 200
        assert len(test_items) == 300

    def test_benchmark_language_balance(self, benchmark_items):
        dev_items = [x for x in benchmark_items if x.get("split") == "dev"]
        test_items = [x for x in benchmark_items if x.get("split") == "test"]

        # Dev set balance
        assert sum(1 for x in dev_items if x["language"] == "khmer") == 80
        assert sum(1 for x in dev_items if x["language"] == "english") == 80
        assert sum(1 for x in dev_items if x["language"] == "khmenglish") == 40

        # Test set balance
        assert sum(1 for x in test_items if x["language"] == "khmer") == 120
        assert sum(1 for x in test_items if x["language"] == "english") == 120
        assert sum(1 for x in test_items if x["language"] == "khmenglish") == 60

    def test_benchmark_schema_integrity(self, benchmark_items):
        for it in benchmark_items:
            assert "id" in it and it["id"]
            assert it["language"] in ("khmer", "english", "khmenglish")
            assert "query" in it and len(it["query"].strip()) > 0
            assert "expected_intent" in it and it["expected_intent"]
            assert "has_active_step" in it
            assert "context" in it


# ─────────────────────────────────────────────────────────────────────────────
# 2. Redacted Telemetry & Safety Audit Store (Task 0.2)
# ─────────────────────────────────────────────────────────────────────────────

class TestTelemetryAndSafetyAudit:

    def test_pipeline_trace_redacts_pii(self):
        raw_msg = "Hello! My name is Alice Johnson and I think 15 is the answer."
        trace = PipelineTrace(
            session_id="test_safe_sess",
            raw_query=raw_msg,
            normalized_query="15",
            rewritten_query="15",
            subject="MATH",
            target_service="MATH_SERVICE",
            service_endpoint="/validate",
            result_summary="Testing PII scrubbing"
        )
        assert "[NAME]" in trace.redacted_query
        assert "Alice Johnson" not in trace.redacted_query

        safe_dict = trace.to_safe_dict()
        assert "Alice Johnson" not in safe_dict["raw_query"]
        assert "[NAME]" in safe_dict["raw_query"]

    def test_tidy_log_renders_sanitized_query(self):
        trace = PipelineTrace(
            session_id="sess_123",
            raw_query="My phone is 012 345 678 and answer is 7",
            normalized_query="7",
            rewritten_query="7",
            subject="MATH",
            target_service="MATH_SERVICE",
            service_endpoint="/validate",
            result_summary="Checking log renderer"
        )
        box = format_tidy_pipeline_log(trace)
        assert "[PHONE]" in box
        assert "012 345 678" not in box

    def test_isolated_safety_audit_store(self):
        store = SafetyAuditStore()
        event = store.record(
            session_id="child_sess_99",
            severity_tier=2,
            category="ABUSE",
            raw_or_scrubbed_text="My uncle John Smith hit me at home",
            action_taken="ESCALATE_SCHOOL_COUNSELOR",
            escalation_channel="school_coordinator"
        )
        assert event.severity_tier == 2
        assert event.category == "ABUSE"
        assert event.escalation_channel == "school_coordinator"
        # Integrity HMAC signature must be present and valid
        assert len(event.integrity_hash) == 64
        assert event.integrity_hash == event.compute_integrity()

        # Check retrieval by session
        session_events = store.get_events_for_session("child_sess_99")
        assert len(session_events) == 1
        assert session_events[0].action_taken == "ESCALATE_SCHOOL_COUNSELOR"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Ingress Routing, Khmer Numerals, & UNCLEAR Degradation (Task 0.3)
# ─────────────────────────────────────────────────────────────────────────────

class TestIngressRoutingAndUnclearDegradation:

    def test_tier1_pure_arabic_number_bypass(self):
        res = classify_student_intent("15", has_active_step=True)
        assert res.intent == INTENT_ANSWER_ATTEMPT
        assert res.confidence == 1.0
        assert res.extracted_answer == "15"
        assert "Tier 1" in res.reason

    def test_tier1_pure_khmer_numeral_bypass(self):
        # Khmer numeral ១៥ -> 15
        res = classify_student_intent("១៥", has_active_step=True)
        assert res.intent == INTENT_ANSWER_ATTEMPT
        assert res.confidence == 1.0
        assert res.extracted_answer == "15"
        assert "Tier 1" in res.reason

    def test_tier1_fraction_and_decimal_bypass(self):
        res_frac = classify_student_intent("3/4", has_active_step=True)
        assert res_frac.intent == INTENT_ANSWER_ATTEMPT
        assert res_frac.confidence == 1.0

        res_dec = classify_student_intent("0.5", has_active_step=True)
        assert res_dec.intent == INTENT_ANSWER_ATTEMPT
        assert res_dec.confidence == 1.0

    def test_tier1_choice_button_bypass(self):
        res = classify_student_intent("B", has_active_step=True)
        assert res.intent == INTENT_ANSWER_ATTEMPT
        assert res.confidence == 1.0

    def test_ambiguous_noise_classified_as_unclear(self):
        for noise in ["...", "???", "!!!", "idk", "huh", "---"]:
            res = classify_student_intent(noise, has_active_step=True)
            assert res.intent == INTENT_UNCLEAR
            assert res.confidence >= INGRESS_CONFIDENCE_THRESHOLD

    def test_unclear_node_handles_first_and_second_turn(self):
        state = {
            "raw_user_input": "...",
            "step_widget": {"steps": [{"step_number": 1, "title": "Step 1"}]},
            "unclear_streak": 0
        }
        updates = classify_intent_node(state)
        assert updates["detected_intent"] == "UNCLEAR"
        assert updates["unclear_streak"] == 1
        assert updates["degrade_to_tap_first"] is False
        assert "I didn't quite catch that" in updates["feedback_message"]

    def test_unclear_node_triggers_tap_first_on_third_consecutive_turn(self):
        state = {
            "raw_user_input": "???",
            "step_widget": {"steps": [{"step_number": 1, "title": "Step 1"}]},
            "unclear_streak": 2  # already had 2 unclear turns
        }
        updates = classify_intent_node(state)
        assert updates["detected_intent"] == "UNCLEAR"
        assert updates["unclear_streak"] == 3
        assert updates["degrade_to_tap_first"] is True
        assert updates["suggested_chips"] is not None
        assert len(updates["suggested_chips"]) >= 3
        assert "tap a clue below or use the number pad" in updates["feedback_message"]

    def test_subsequent_valid_answer_resets_unclear_streak(self):
        state = {
            "raw_user_input": "15",
            "step_widget": {"steps": [{"step_number": 1, "title": "Step 1"}]},
            "unclear_streak": 3,
            "degrade_to_tap_first": True
        }
        updates = classify_intent_node(state)
        assert updates["detected_intent"] == INTENT_ANSWER_ATTEMPT
        assert updates["unclear_streak"] == 0
        assert updates["degrade_to_tap_first"] is False
        assert updates["student_attempt"] == "15"
