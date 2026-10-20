"""
File: backend/testing/unit/socratic/test_sprint2_schema_invariants.py
Description: Unit test suite for Sprint 2:
             1. Structured Interpretation Schema, Correction Markers & Disjunctive Inquiries (Task 2.1)
             2. Number Traceability Invariant Verifier (Task 2.2)
             3. State-Aware Numeric-Token Leak Checker & Proximity Gating (Task 2.3)
"""

# pyrefly: ignore [missing-import]
import os
import sys
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
from app.services.nlu.interpretation_schema import (
    StudentInterpretation,
    has_correction_marker,
    is_disjunctive_inquiry,
    resolve_answer_candidates
)
# pyrefly: ignore [missing-import]
from app.services.socratic.invariants import (
    extract_raw_input_numeric_tokens,
    verify_number_traceability
)
# pyrefly: ignore [missing-import]
from app.services.socratic.leak_checker import (
    check_tutor_response_leak,
    SAFE_CLUE_FALLBACK
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Structured Schema, Correction Markers & Disjunctive Inquiries (Task 2.1)
# ─────────────────────────────────────────────────────────────────────────────

class TestInterpretationSchemaAndCorrectionMarkers:

    def test_english_correction_marker_adopts_last_candidate(self):
        text = "I think it is 10, no wait 15"
        candidates = ["10", "15"]
        assert has_correction_marker(text) is True
        resolved, reason = resolve_answer_candidates(text, candidates)
        assert resolved == "15"
        assert reason == "correction_marker_applied"

    def test_khmer_correction_marker_adopts_last_candidate(self):
        text = "ខ្ញុំគិតថា ៨ អត់ទេ ៩ វិញ"
        candidates = ["8", "9"]
        assert has_correction_marker(text) is True
        resolved, reason = resolve_answer_candidates(text, candidates)
        assert resolved == "9"
        assert reason == "correction_marker_applied"

    def test_disjunctive_inquiry_does_not_adopt_candidate(self):
        # "Is it 14 or 15?" must never adopt 15 as student's answer
        text = "Is it 14 or 15?"
        candidates = ["14", "15"]
        assert is_disjunctive_inquiry(text) is True
        resolved, reason = resolve_answer_candidates(text, candidates)
        assert resolved is None
        assert reason == "disjunctive_inquiry"

    def test_khmer_disjunctive_inquiry_rejected(self):
        text = "តើ ៧ ឬ ៨?"
        candidates = ["7", "8"]
        assert is_disjunctive_inquiry(text) is True
        resolved, reason = resolve_answer_candidates(text, candidates)
        assert resolved is None
        assert reason == "disjunctive_inquiry"

    def test_single_candidate_resolved(self):
        text = "I think 42"
        candidates = ["42"]
        resolved, reason = resolve_answer_candidates(text, candidates)
        assert resolved == "42"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Number Traceability Invariant Verifier (Task 2.2)
# ─────────────────────────────────────────────────────────────────────────────

class TestNumberTraceabilityInvariant:

    def test_traceable_arabic_numerals(self):
        raw = "My answer is 15 cookies"
        candidates = ["15"]
        ok, valid, hallucinated = verify_number_traceability(raw, candidates)
        assert ok is True
        assert valid == ["15"]
        assert len(hallucinated) == 0

    def test_traceable_khmer_numerals(self):
        raw = "ចម្លើយគឺ ៣/៤"
        candidates = ["3/4"]
        ok, valid, hallucinated = verify_number_traceability(raw, candidates)
        assert ok is True
        assert valid == ["3/4"]

    def test_traceable_english_number_words(self):
        raw = "I got fifteen apples"
        candidates = ["15"]
        ok, valid, hallucinated = verify_number_traceability(raw, candidates)
        assert ok is True
        assert valid == ["15"]

    def test_hallucinated_number_rejected(self):
        raw = "I think it is green leaves"
        # Model hallucinated 42
        candidates = ["42"]
        ok, valid, hallucinated = verify_number_traceability(raw, candidates)
        assert ok is False
        assert len(valid) == 0
        assert hallucinated == ["42"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. State-Aware Numeric-Token Leak Checker (Task 2.3)
# ─────────────────────────────────────────────────────────────────────────────

class TestStateAwareNumericLeakChecker:

    def test_solved_step_allows_praise_with_answer(self):
        reply = "🎉 Fantastic! 15 is the correct answer!"
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=True,
            current_hint_tier=0
        )
        assert is_leak is False
        assert final_reply == reply
        assert reason == "state_allows_answer"

    def test_hint_tier_3_allows_reveal(self):
        reply = "Here is how we solve it: the result is 15."
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            is_reveal_state=True,
            current_hint_tier=3
        )
        assert is_leak is False
        assert final_reply == reply
        assert reason == "state_allows_answer"

    def test_unsolved_step_blocks_direct_leak(self):
        reply = "Try calculating it: the answer is 15."
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            current_hint_tier=1
        )
        assert is_leak is True
        assert final_reply == SAFE_CLUE_FALLBACK
        assert "numeric_answer_leak" in reason

    def test_unsolved_step_blocks_expression_leak(self):
        reply = "Notice that you can divide: 30/2 gives the value."
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            current_hint_tier=1
        )
        assert is_leak is True
        assert final_reply == SAFE_CLUE_FALLBACK

    def test_benign_step_label_does_not_false_positive(self):
        # Target answer is 2, but tutor says "Step 2"
        reply = "Welcome to Step 2! Count the cookies in the picture."
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="2",
            is_step_solved=False,
            current_hint_tier=0
        )
        assert is_leak is False
        assert final_reply == reply

    def test_decimal_subvalue_does_not_false_positive(self):
        # Target answer is 15, reply mentions 15.3
        reply = "The temperature increased to 15.3 degrees."
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            current_hint_tier=0
        )
        assert is_leak is False
        assert final_reply == reply

    def test_proximity_feedback_gated_to_first_attempt(self):
        reply = "You're just 1 away! Try again!"
        # First attempt: allowed
        is_leak1, final1, reason1 = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            attempts_count=1
        )
        assert is_leak1 is False
        assert "just 1 away" in final1

        # Second attempt: sanitized to prevent guessing game
        is_leak2, final2, reason2 = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            attempts_count=2
        )
        assert is_leak2 is False
        assert "just 1 away" not in final2
        assert reason2 == "proximity_feedback_constrained"
