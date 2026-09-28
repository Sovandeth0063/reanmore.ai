"""
Unit Tests for Day 9: Step Context Disambiguation & Short Answer Extractor.
Validates single-token and short student answers, help/stuck detection,
and active step context vs out-of-context differentiation.
"""

import os
import sys
# pyrefly: ignore [missing-import]
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

# pyrefly: ignore [missing-import]
from app.services.nlu import (  # type: ignore
    IntentType,
    IntentResult,
    classify_intent,
    classify_intent_sync,
    classify_intent_heuristic,
    disambiguate_step_input,
    is_step_active,
    format_chat_history,
    extract_core_answer,
)


@pytest.fixture
def active_math_step():
    return {
        "step_num": 1,
        "expression": "2 + 2",
        "expected_answer": "4",
        "hint": "Think about adding two pairs of apples."
    }


@pytest.fixture
def active_science_step():
    return {
        "step_num": 2,
        "prompt": "In which plant cell organelle does photosynthesis take place?",
        "expected_answer": "chloroplast",
        "hint": "It contains the green pigment chlorophyll."
    }


class TestStepActivationHelper:
    """Verify is_step_active helper logic."""

    def test_active_with_data(self, active_math_step):
        assert is_step_active(active_math_step) is True

    def test_active_with_step_index_zero(self):
        assert is_step_active({"step_index": 0}) is True

    def test_inactive_when_none(self):
        assert is_step_active(None) is False

    def test_inactive_when_empty_dict(self):
        assert is_step_active({}) is False

    def test_inactive_when_explicit_false_flag(self):
        assert is_step_active({"active": False, "step_num": 1}) is False

    def test_inactive_when_values_empty(self):
        assert is_step_active({"step": "", "prompt": None}) is False


class TestNumericalShortAnswers:
    """Verify single-token and short numerical answers during active steps."""

    def test_single_digit_number(self, active_math_step):
        res = classify_intent_sync("4", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.confidence >= 0.95
        assert res.extracted_answer == "4"

    def test_multi_digit_number(self, active_math_step):
        res = classify_intent_sync("12", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "12"

    def test_fraction_answer(self, active_math_step):
        res = classify_intent_sync("3/4", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "3/4"

    def test_decimal_answer(self, active_math_step):
        res = classify_intent_sync("0.5", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "0.5"

    def test_negative_number(self, active_math_step):
        res = classify_intent_sync("-7", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "-7"


class TestScientificTermsShortAnswers:
    """Verify scientific vocabulary tokens resolved as STEP_ATTEMPT during active step."""

    def test_chloroplast(self, active_science_step):
        res = classify_intent_sync("chloroplast", current_step=active_science_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "chloroplast"

    def test_photosynthesis(self, active_science_step):
        res = classify_intent_sync("photosynthesis", current_step=active_science_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "photosynthesis"

    def test_gravity(self, active_science_step):
        res = classify_intent_sync("gravity", current_step=active_science_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "gravity"

    def test_liquid(self, active_science_step):
        res = classify_intent_sync("liquid", current_step=active_science_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "liquid"


class TestBooleanConfirmations:
    """Verify boolean responses ('yes', 'no', 'true', 'false') during active steps."""

    def test_yes(self, active_math_step):
        res = classify_intent_sync("yes", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "yes"

    def test_no(self, active_math_step):
        res = classify_intent_sync("no", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "no"

    def test_true(self, active_math_step):
        res = classify_intent_sync("true", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "true"


class TestUnitsWithValues:
    """Verify units attached to values ('5 cm', '10 kg', '12 cookies')."""

    def test_length_units(self, active_math_step):
        res = classify_intent_sync("5 cm", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "5 cm"

    def test_mass_units(self, active_math_step):
        res = classify_intent_sync("10 kg", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "10 kg"

    def test_object_unit_words_cleaned(self, active_math_step):
        res = classify_intent_sync("12 cookies", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "12"


class TestConversationalHedging:
    """Verify conversational phrasing stripped to core answer during active steps."""

    def test_i_think_prefix(self, active_math_step):
        res = classify_intent_sync("I think 12", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "12"

    def test_it_happens_in_prefix(self, active_science_step):
        res = classify_intent_sync("It happens in the chloroplast", current_step=active_science_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "chloroplast"

    def test_maybe_with_question_mark(self, active_math_step):
        res = classify_intent_sync("maybe 3/4?", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "3/4"

    def test_is_it_prefix(self, active_math_step):
        res = classify_intent_sync("is it 5?", current_step=active_math_step)
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "5"


class TestHelpAndStuckSeeking:
    """Verify help-seeking expressions route to CLARIFY during active steps."""

    @pytest.mark.parametrize("phrase", [
        "idk",
        "i don't know",
        "i dont know",
        "help",
        "help me",
        "hint please",
        "hint",
        "give me a hint",
        "clue please",
        "what next",
        "i'm stuck",
        "im stuck",
        "not sure",
        "i don't get it",
    ])
    def test_help_seeking_routes_to_clarify(self, phrase, active_math_step):
        res = classify_intent_sync(phrase, current_step=active_math_step)
        assert res.intent == IntentType.CLARIFY
        assert res.confidence >= 0.95


class TestContextDifferentiation:
    """Verify contrast between query with active step vs without active step."""

    def test_number_with_and_without_step(self, active_math_step):
        # Without context or history -> INITIAL_SOLVE
        without_ctx = classify_intent_sync("4")
        assert without_ctx.intent == IntentType.INITIAL_SOLVE

        # With active step context -> STEP_ATTEMPT
        with_ctx = classify_intent_sync("4", current_step=active_math_step)
        assert with_ctx.intent == IntentType.STEP_ATTEMPT
        assert with_ctx.extracted_answer == "4"

    def test_scientific_term_with_and_without_step(self, active_science_step):
        without_ctx = classify_intent_sync("chloroplast")
        assert without_ctx.intent == IntentType.INITIAL_SOLVE

        with_ctx = classify_intent_sync("chloroplast", current_step=active_science_step)
        assert with_ctx.intent == IntentType.STEP_ATTEMPT
        assert with_ctx.extracted_answer == "chloroplast"


class TestChitchatAndPracticePriority:
    """Ensure chitchat and practice requests are still respected during an active step."""

    def test_greetings_during_step(self, active_math_step):
        res = classify_intent_sync("hi", current_step=active_math_step)
        assert res.intent == IntentType.CHITCHAT

    def test_gratitude_during_step(self, active_math_step):
        res = classify_intent_sync("thanks so much", current_step=active_math_step)
        assert res.intent == IntentType.CHITCHAT

    def test_farewell_during_step(self, active_math_step):
        res = classify_intent_sync("bye", current_step=active_math_step)
        assert res.intent == IntentType.CHITCHAT

    def test_practice_request_during_step(self, active_math_step):
        res = classify_intent_sync("give me another practice problem", current_step=active_math_step)
        assert res.intent == IntentType.REQUEST_PRACTICE

    def test_clarification_question_during_step(self, active_science_step):
        res = classify_intent_sync("What is chlorophyll?", current_step=active_science_step)
        assert res.intent == IntentType.CLARIFY


class TestDisambiguateStepInputDirect:
    """Direct testing of disambiguate_step_input engine function."""

    def test_returns_none_when_no_step(self):
        res = disambiguate_step_input("4", current_step=None)
        assert res is None

    def test_returns_none_when_empty_dict(self):
        res = disambiguate_step_input("4", current_step={})
        assert res is None

    def test_returns_none_when_inactive_flag(self):
        res = disambiguate_step_input("4", current_step={"active": False, "step_num": 1})
        assert res is None

    def test_returns_step_attempt_when_active(self, active_math_step):
        res = disambiguate_step_input("4", current_step=active_math_step)
        assert res is not None
        assert res.intent == IntentType.STEP_ATTEMPT
        assert res.extracted_answer == "4"

    def test_question_not_hijacked_as_step_attempt(self, active_math_step):
        # Asking a question during an active step must NOT be hijacked as a step attempt
        res = disambiguate_step_input("What comes after 19?", current_step=active_math_step)
        assert res is not None
        assert res.intent == IntentType.INITIAL_SOLVE


class TestNewQuestionDuringActiveStep:
    """Verifies that asking a new question during an active problem routes to INITIAL_SOLVE or CLARIFY."""

    def test_what_comes_after_19(self, active_math_step):
        res = classify_intent_sync("What comes after 19?", current_step=active_math_step)
        assert res.intent == IntentType.INITIAL_SOLVE

    def test_math_equation_question(self, active_math_step):
        res = classify_intent_sync("what is 5+5?", current_step=active_math_step)
        assert res.intent == IntentType.INITIAL_SOLVE

    def test_new_science_problem(self, active_math_step):
        res = classify_intent_sync("solve: photosynthesis needs sunlight and water", current_step=active_math_step)
        assert res.intent == IntentType.INITIAL_SOLVE

    def test_khmer_question(self, active_math_step):
        res = classify_intent_sync("តើលេខបន្ទាប់ពី 19 គឺជាអ្វី?", current_step=active_math_step)
        assert res.intent == IntentType.INITIAL_SOLVE

    def test_short_valid_answers_remain_step_attempt(self, active_math_step, active_science_step):
        res1 = classify_intent_sync("4", current_step=active_math_step)
        assert res1.intent == IntentType.STEP_ATTEMPT
        assert res1.extracted_answer == "4"

        res2 = classify_intent_sync("chloroplast", current_step=active_science_step)
        assert res2.intent == IntentType.STEP_ATTEMPT
        assert res2.extracted_answer == "chloroplast"


class TestChatHistoryWithActiveStep:
    """Verify format_chat_history incorporates active step information."""

    def test_history_includes_current_step(self, active_math_step):
        formatted = format_chat_history(current_step=active_math_step)
        assert "Current Active Step:" in formatted
        assert "2 + 2" in formatted


@pytest.mark.asyncio
async def test_async_classify_intent_with_current_step(active_math_step):
    """Verify async master entrypoint fast-paths disambiguation with current_step."""
    res = await classify_intent("4", current_step=active_math_step)
    assert isinstance(res, IntentResult)
    assert res.intent == IntentType.STEP_ATTEMPT
    assert res.extracted_answer == "4"
