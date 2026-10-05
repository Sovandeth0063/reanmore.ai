"""
Unit tests for Sprint 1 new backend nodes:
  - intent_classifier.py  (Task 1.4)
  - reveal_and_continue.py (Task 1.3)
"""

# pyrefly: ignore [missing-import]
import pytest
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

# pyrefly: ignore [missing-import]
from app.services.socratic.intent_classifier import (
    classify_student_intent,
    INTENT_ANSWER_ATTEMPT,
    INTENT_CLARIFICATION,
    INTENT_OFF_TOPIC,
    INTENT_ANSWER_DEMAND,
    INTENT_SAFETY,
)
# pyrefly: ignore [missing-import]
from app.services.socratic.reveal_and_continue import (
    compute_frustration_score,
    build_reveal_message,
    should_offer_break,
)


# ─────────────────────────────────────────────────────────────────────────────
# Intent Classifier Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentClassifier:
    """Tests for classify_student_intent()."""

    def test_short_number_is_answer_attempt(self):
        result = classify_student_intent("42", has_active_step=True)
        assert result.intent == INTENT_ANSWER_ATTEMPT
        assert result.extracted_answer == "42"

    def test_fraction_answer_is_attempt(self):
        result = classify_student_intent("1/2", has_active_step=True)
        assert result.intent == INTENT_ANSWER_ATTEMPT

    def test_answer_demand_just_tell_me(self):
        result = classify_student_intent("just tell me the answer", has_active_step=True)
        assert result.intent == INTENT_ANSWER_DEMAND

    def test_answer_demand_give_me_answer(self):
        result = classify_student_intent("give me the answer please", has_active_step=True)
        assert result.intent == INTENT_ANSWER_DEMAND

    def test_answer_demand_khmer(self):
        result = classify_student_intent("ប្រាប់ចម្លើយ", has_active_step=True)
        assert result.intent == INTENT_ANSWER_DEMAND

    def test_off_topic_tired(self):
        result = classify_student_intent("I'm tired", has_active_step=False)
        assert result.intent == INTENT_OFF_TOPIC

    def test_off_topic_bored(self):
        result = classify_student_intent("this is boring", has_active_step=False)
        assert result.intent == INTENT_OFF_TOPIC

    def test_safety_hurt(self):
        result = classify_student_intent("someone is hurting me", has_active_step=True)
        assert result.intent == INTENT_SAFETY
        assert result.confidence >= 0.9

    def test_safety_scared(self):
        result = classify_student_intent("I am scared of him", has_active_step=False)
        assert result.intent == INTENT_SAFETY

    def test_clarification_how_to(self):
        result = classify_student_intent("how do I do this step?", has_active_step=True)
        assert result.intent == INTENT_CLARIFICATION

    def test_clarification_hint_keyword(self):
        result = classify_student_intent("can I get a hint please", has_active_step=True)
        assert result.intent == INTENT_CLARIFICATION

    def test_clarification_dont_understand(self):
        result = classify_student_intent("I don't understand this question", has_active_step=True)
        assert result.intent == INTENT_CLARIFICATION

    def test_science_word_answer_is_attempt(self):
        result = classify_student_intent("photosynthesis", has_active_step=True)
        assert result.intent == INTENT_ANSWER_ATTEMPT

    def test_yes_no_answer_is_attempt(self):
        result = classify_student_intent("yes", has_active_step=True)
        assert result.intent == INTENT_ANSWER_ATTEMPT

    def test_no_active_step_question_is_offtopic(self):
        result = classify_student_intent("what is 7 times 8", has_active_step=False)
        # Without active step, it should fall through to off-topic or attempt
        assert result.intent in (INTENT_OFF_TOPIC, INTENT_ANSWER_ATTEMPT)

    def test_safety_takes_priority_over_answer_demand(self):
        # Contains both demand and safety signals
        result = classify_student_intent("just tell me, I want to hurt myself", has_active_step=True)
        assert result.intent == INTENT_SAFETY


# ─────────────────────────────────────────────────────────────────────────────
# Frustration Score Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFrustrationScore:
    """Tests for compute_frustration_score()."""

    def test_zero_history_zero_score(self):
        score = compute_frustration_score([], None, None)
        assert score == 0.0

    def test_one_wrong_gives_0_2(self):
        history = [{"is_correct": False}]
        score = compute_frustration_score(history, None, None)
        assert abs(score - 0.2) < 0.01

    def test_three_consecutive_wrong_gives_0_6(self):
        history = [
            {"is_correct": False},
            {"is_correct": False},
            {"is_correct": False},
        ]
        score = compute_frustration_score(history, None, None)
        assert abs(score - 0.6) < 0.01

    def test_correct_break_resets_consecutive(self):
        history = [
            {"is_correct": False},
            {"is_correct": True},   # break
            {"is_correct": False},
        ]
        score = compute_frustration_score(history, None, None)
        # Only 1 consecutive wrong at tail → 0.2
        assert abs(score - 0.2) < 0.01

    def test_fast_guess_adds_0_3(self):
        score = compute_frustration_score([], response_time_ms=1500, idle_seconds=None)
        assert abs(score - 0.3) < 0.01

    def test_idle_adds_0_2(self):
        score = compute_frustration_score([], response_time_ms=None, idle_seconds=120)
        assert abs(score - 0.2) < 0.01

    def test_all_signals_capped_at_1(self):
        history = [{"is_correct": False}] * 5
        score = compute_frustration_score(history, response_time_ms=1000, idle_seconds=120)
        assert score <= 1.0

    def test_should_offer_break_threshold(self):
        assert should_offer_break(0.85) is True
        assert should_offer_break(0.79) is False
        assert should_offer_break(0.80) is True


# ─────────────────────────────────────────────────────────────────────────────
# Reveal Message Builder Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRevealMessageBuilder:
    """Tests for build_reveal_message()."""

    def test_math_addition_worked_example(self):
        msg = build_reveal_message(
            step_number=1,
            mission="What is 5 + 3?",
            expected_answer="8",
            clue="Add the two numbers together",
            attempt_history=[{"is_correct": False}] * 3,
        )
        assert "8" in msg
        assert "Worked Example" in msg
        assert "Step 1" in msg

    def test_science_plant_worked_example(self):
        msg = build_reveal_message(
            step_number=2,
            mission="What do plants need for photosynthesis?",
            expected_answer="sunlight and water",
            clue="Think about what you water a plant with",
            attempt_history=[{"is_correct": False}] * 3,
        )
        assert "Worked Example" in msg
        assert "sunlight and water" in msg

    def test_subtraction_worked_example(self):
        msg = build_reveal_message(
            step_number=1,
            mission="10 minus 4 = ?",
            expected_answer="6",
            clue="Take away 4 from 10",
            attempt_history=[{"is_correct": False}] * 3,
        )
        assert "6" in msg

    def test_does_not_show_answer_before_worked_example(self):
        msg = build_reveal_message(
            step_number=1,
            mission="What is 7 + 5?",
            expected_answer="12",
            clue="Add the two numbers",
            attempt_history=[{"is_correct": False}] * 3,
        )
        # Worked example should appear before the answer reveal
        worked_idx = msg.find("Worked Example")
        answer_idx = msg.find("The answer to Step")
        assert worked_idx < answer_idx

    def test_includes_encouragement(self):
        msg = build_reveal_message(
            step_number=1,
            mission="Count the birds",
            expected_answer="3",
            clue="Count each bird",
            attempt_history=[{"is_correct": False}] * 3,
        )
        # Should contain some form of encouragement
        assert any(w in msg for w in ["perseverance", "effort", "tries", "best shot"])
