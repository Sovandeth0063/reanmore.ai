"""
File: backend/testing/unit/socratic/test_leak_guard_stage.py
Description: Exhaustive unit and benchmark validation for the Output Leak Guard stage (Phase 4).
             - Verifies word-to-number expansion, numeric equivalence, concept keywords.
             - Verifies strict Tier 3 prohibition (Tier 3 hints must NEVER reveal answers).
             - Verifies multi-step praise shielding for future unsolved steps.
             - Verifies LangGraph System 2 output stage integration and quarantine.
             - Executes the 120-item leak_adversarial_benchmark.jsonl suite (target: 0% leaks).
"""

import json
from pathlib import Path
import pytest

from app.services.guardrails.leak_guard import (
    LeakGuard,
    check_tutor_response_leak,
    check_response_for_leaks,
    SAFE_CLUE_FALLBACK_ENG,
    SAFE_PRAISE_FALLBACK_ENG,
)
from app.services.socratic.card_schema import SocraticStep, StepWidgetPayload
from app.services.socratic.graph import compile_response_node

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


# =========================================================================
# 1. Word-to-Number & Arithmetic Expression Equivalence Tests
# =========================================================================

class TestLeakGuardWordAndMathEquivalence:
    def setup_method(self):
        self.guard = LeakGuard()

    def test_composite_english_number_words(self):
        # Target 25, tutor says "twenty five"
        leak, final, reason = check_tutor_response_leak(
            tutor_reply="The remaining amount is twenty five items.",
            target_answer="25",
            is_step_solved=False
        )
        assert leak is True
        assert "numeric_answer_leak_detected" in reason
        assert final == SAFE_CLUE_FALLBACK_ENG

        # Hyphenated "twenty-five"
        leak_hyphen, _, _ = check_tutor_response_leak(
            tutor_reply="The remaining amount is twenty-five.",
            target_answer="25",
            is_step_solved=False
        )
        assert leak_hyphen is True

    def test_word_arithmetic_expressions(self):
        # "half of 30" -> 15
        leak, _, _ = check_tutor_response_leak(
            tutor_reply="Take half of 30 to get the count.",
            target_answer="15",
            is_step_solved=False
        )
        assert leak is True

        # "thirty divided by two" -> 15
        leak_div, _, _ = check_tutor_response_leak(
            tutor_reply="Calculate thirty divided by two.",
            target_answer="15",
            is_step_solved=False
        )
        assert leak_div is True

        # "ten plus five" -> 15
        leak_add, _, _ = check_tutor_response_leak(
            tutor_reply="Think about ten plus five.",
            target_answer="15",
            is_step_solved=False
        )
        assert leak_add is True

        # "three times five" -> 15
        leak_mul, _, _ = check_tutor_response_leak(
            tutor_reply="Notice that three times five gives our goal.",
            target_answer="15",
            is_step_solved=False
        )
        assert leak_mul is True

    def test_khmer_number_words_and_numerals(self):
        # Khmer numerals "១៥" -> 15
        leak_km, _, _ = check_tutor_response_leak(
            tutor_reply="ចម្លើយគឺ ១៥",
            target_answer="15",
            is_step_solved=False
        )
        assert leak_km is True

        # Khmer word "ដប់ប្រាំ" -> 15
        leak_km_w, _, _ = check_tutor_response_leak(
            tutor_reply="ចំនួនគឺ ដប់ប្រាំ",
            target_answer="15",
            is_step_solved=False
        )
        assert leak_km_w is True

    def test_thousands_and_decimals(self):
        # Thousands comma "1,500" matches 1500
        leak_thous, _, _ = check_tutor_response_leak(
            tutor_reply="The total cost is 1,500 riel.",
            target_answer="1500",
            is_step_solved=False
        )
        assert leak_thous is True

        # "1,500" does not leak 15
        leak_diff, _, _ = check_tutor_response_leak(
            tutor_reply="The total cost is 1,500 riel.",
            target_answer="15",
            is_step_solved=False
        )
        assert leak_diff is False


# =========================================================================
# 2. Science Concept Keyword Leak Defense
# =========================================================================

class TestLeakGuardConceptKeywords:
    def test_short_science_concept_leaks(self):
        # "gas" as target answer
        leak_gas, _, reason = check_tutor_response_leak(
            tutor_reply="When water boils, it turns into a gas.",
            target_answer="gas",
            is_step_solved=False
        )
        assert leak_gas is True
        assert "concept_word_leak_detected" in reason

        # "ice" as target answer
        leak_ice, _, _ = check_tutor_response_leak(
            tutor_reply="Frozen water is called ice.",
            target_answer="ice",
            is_step_solved=False
        )
        assert leak_ice is True

    def test_long_science_concept_leaks(self):
        leak_photo, _, _ = check_tutor_response_leak(
            tutor_reply="Plants produce glucose through photosynthesis.",
            target_answer="photosynthesis",
            is_step_solved=False
        )
        assert leak_photo is True

    def test_stop_words_do_not_false_positive(self):
        # Common word "in" or "is" should not cause false positive if not educational target
        leak_clean, _, _ = check_tutor_response_leak(
            tutor_reply="Look at the water in the cup.",
            target_answer="condensation",
            is_step_solved=False
        )
        assert leak_clean is False


# =========================================================================
# 3. Strict Tier 3 Socratic Prohibition & State Rules
# =========================================================================

class TestLeakGuardTier3AndStateRules:
    def test_tier3_strictly_forbids_answer_disclosure(self):
        # Even at current_hint_tier=3, answer disclosure is forbidden without explicit reveal state
        leak, final, reason = check_tutor_response_leak(
            tutor_reply="At Tier 3, the answer is 42.",
            target_answer="42",
            is_step_solved=False,
            is_reveal_state=False,
            current_hint_tier=3,
            attempts_count=3
        )
        assert leak is True
        assert "numeric_answer_leak_detected" in reason
        assert final == SAFE_CLUE_FALLBACK_ENG

    def test_explicit_reveal_state_permits_active_step_answer(self):
        # When is_reveal_state=True (triggered by reveal_and_continue_node), active answer is allowed
        reply = "Here is the solution: The answer to this step is 42."
        leak, final, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="42",
            is_step_solved=False,
            is_reveal_state=True,
            current_hint_tier=3
        )
        assert leak is False
        assert reason == "state_allows_answer"
        assert final == reply

    def test_multi_step_praise_shield_blocks_future_step_leaks(self):
        # Step 1 is solved (15), but reply accidentally leaks Step 2 target (25)
        leak, final, reason = check_tutor_response_leak(
            tutor_reply="Great job solving 15! In the next step we need to find 25.",
            target_answer="15",
            is_step_solved=True,
            unsolved_step_values=["25", "40"],
            final_answer="40"
        )
        assert leak is True
        assert "unsolved_future_step_leak_detected" in reason
        assert final == SAFE_PRAISE_FALLBACK_ENG

    def test_multi_step_praise_allows_current_step_answer(self):
        # Step 1 is solved (15), praise mentions only 15
        leak, final, reason = check_tutor_response_leak(
            tutor_reply="🌟 Spot on! 15 is correct! Let's examine step 2.",
            target_answer="15",
            is_step_solved=True,
            unsolved_step_values=["25", "40"],
            final_answer="40"
        )
        assert leak is False
        assert reason == "state_allows_answer"


# =========================================================================
# 4. LangGraph Output Stage Integration & Quarantine
# =========================================================================

class TestLangGraphOutputLeakGuardStage:
    def test_compile_response_node_quarantines_leaked_feedback(self):
        step1 = SocraticStep(
            step_number=1,
            title="Count Marbles",
            mission="Count the blue marbles",
            clue="Group them in pairs",
            helpful_example="2 pairs = 4",
            your_turn="How many blue marbles?",
            expected_answer="14"
        )
        widget = StepWidgetPayload(
            total_steps=1,
            current_step_index=0,
            completed_steps=[],
            steps=[step1]
        )

        # State with a simulated leaking tutor message
        state = {
            "session_id": "test_sess_001",
            "step_widget": widget.model_dump(),
            "feedback_message": "The answer to this question is 14!",
            "active_hint": "Try 14.",
            "is_problem_complete": False,
            "validation_outcome": "INCORRECT",
            "is_reveal_state": False,
            "current_hint_tier": 2,
            "attempt_history": [{"attempt": "10", "is_correct": False}],
            "is_safe": True
        }

        output = compile_response_node(state)

        # Assert Output Leak Guard intercepted and quarantined the leak
        assert output.get("leak_quarantined") is True
        assert "14" not in output["feedback_message"]
        assert "14" not in output["active_hint"]
        assert "14" not in output["formatted_markdown"]
        assert output["feedback_message"] == SAFE_CLUE_FALLBACK_ENG

    def test_compile_response_node_permits_clean_message(self):
        step1 = SocraticStep(
            step_number=1,
            title="Count Marbles",
            mission="Count the blue marbles",
            clue="Group them in pairs",
            helpful_example="2 pairs = 4",
            your_turn="How many blue marbles?",
            expected_answer="14"
        )
        widget = StepWidgetPayload(
            total_steps=1,
            current_step_index=0,
            completed_steps=[],
            steps=[step1]
        )

        clean_feedback = "Gently rethink your count! Try pairing them up."
        state = {
            "session_id": "test_sess_002",
            "step_widget": widget.model_dump(),
            "feedback_message": clean_feedback,
            "active_hint": "Look at the pairs.",
            "is_problem_complete": False,
            "validation_outcome": "INCORRECT",
            "is_reveal_state": False,
            "current_hint_tier": 1,
            "is_safe": True
        }

        output = compile_response_node(state)
        assert output.get("leak_quarantined") is not True
        assert output["feedback_message"] == clean_feedback

    def test_compile_response_node_quarantines_leaked_step_hints(self):
        """Hints rendered directly by the step cards must satisfy the leak guard."""
        step1 = SocraticStep(
            step_number=1,
            title="Name the State",
            status="in_progress",
            mission="Match the observation to a state of matter",
            clue="Notice how the steam spreads out to fill the air",
            helpful_example="In Maya's lab, a balloon spreads out to fill with air.",
            your_turn="Since steam spreads out to fill the air, which state of matter is it?",
            expected_answer="Gas",
            hints=[
                "Steam is a gas that floats away.",
                "Solids keep a shape and liquids flow. What about steam?",
                "Does steam keep a shape like a rock? No. Does it stay in a puddle? No. It spreads out.",
            ],
        )
        widget = StepWidgetPayload(
            total_steps=1,
            current_step_index=0,
            completed_steps=[],
            steps=[step1],
        )

        state = {
            "session_id": "test_sess_003",
            "step_widget": widget.model_dump(),
            "feedback_message": None,
            "active_hint": None,
            "is_problem_complete": False,
            "validation_outcome": "INCORRECT",
            "is_reveal_state": False,
            "current_hint_tier": 1,
            "is_safe": True,
        }

        output = compile_response_node(state)

        assert output.get("leak_quarantined") is True
        hints = output["step_widget"]["steps"][0]["hints"]
        assert all("gas" not in h.lower() for h in hints)

    def test_compile_response_node_quarantines_leaked_card_text(self):
        """Mission, clue, and parallel example must not name the expected answer."""
        step1 = SocraticStep(
            step_number=1,
            title="Name the State",
            status="in_progress",
            mission="Name the gas that steam becomes.",
            clue="Matter that spreads out to fill a space is called a gas.",
            helpful_example="The balloon fills with air, so Noah knows it is a gas.",
            your_turn="Since steam spreads out to fill the air, which state of matter is it?",
            expected_answer="Gas",
        )
        widget = StepWidgetPayload(
            total_steps=1,
            current_step_index=0,
            completed_steps=[],
            steps=[step1],
        )
        state = {
            "session_id": "test_sess_004",
            "step_widget": widget.model_dump(),
            "feedback_message": None,
            "active_hint": None,
            "is_problem_complete": False,
            "validation_outcome": "INCORRECT",
            "is_reveal_state": False,
            "current_hint_tier": 0,
            "is_safe": True,
        }

        output = compile_response_node(state)

        assert output.get("leak_quarantined") is True
        rendered = output["step_widget"]["steps"][0]
        for field in ("mission", "clue", "helpful_example"):
            assert "gas" not in rendered[field].lower(), field


# =========================================================================
# 5. Adversarial Leak Benchmark Runner (120 items, Target: 0% leaks)
# =========================================================================

def test_run_leak_adversarial_benchmark_zero_leaks():
    benchmark_file = DATA_DIR / "leak_adversarial_benchmark.jsonl"
    assert benchmark_file.exists(), f"Benchmark file not found at {benchmark_file}"

    total_tested = 0
    leaks_escaped = 0

    with open(benchmark_file, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            total_tested += 1

            d_type = item.get("type")
            tutor_reply = item.get("simulated_tutor_reply", "")
            forbidden_tokens = item.get("forbidden_tokens", [])
            problem_text = item.get("problem_text")
            unsolved_steps = item.get("unsolved_future_steps", [])
            final_ans = item.get("final_answer")

            if d_type == "near_miss_derivation_probe":
                target_ans = item.get("target_answer", "")
                is_leak, sanitized_reply, _ = check_tutor_response_leak(
                    tutor_reply=tutor_reply,
                    target_answer=target_ans,
                    is_step_solved=False,
                    is_reveal_state=False,
                    unsolved_step_values=unsolved_steps,
                    final_answer=final_ans,
                    problem_text=problem_text
                )
                effective_reply = sanitized_reply if is_leak else tutor_reply

            elif d_type == "multi_step_praise_test":
                solved_val = item.get("solved_step_value", "")
                is_leak, sanitized_reply, _ = check_tutor_response_leak(
                    tutor_reply=tutor_reply,
                    target_answer=solved_val,
                    is_step_solved=True,
                    unsolved_step_values=unsolved_steps,
                    final_answer=final_ans,
                    problem_text=problem_text
                )
                effective_reply = sanitized_reply if is_leak else tutor_reply

            else:
                continue

            # Invariant: effective reply MUST NOT leak ANY forbidden token!
            for tok in forbidden_tokens:
                # Check exact whole-word/digit match
                import re
                if re.search(rf"\b{re.escape(tok)}\b", effective_reply):
                    leaks_escaped += 1
                    pytest.fail(
                        f"Leak escaped at line {line_no} ({item.get('dialogue_id')}): "
                        f"Forbidden token '{tok}' found in reply: '{effective_reply}'"
                    )

    assert total_tested == 120, f"Expected 120 benchmark items, found {total_tested}"
    assert leaks_escaped == 0, f"Benchmark failed with {leaks_escaped} answer leaks!"
