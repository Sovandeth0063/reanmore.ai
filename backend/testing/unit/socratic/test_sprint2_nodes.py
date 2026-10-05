"""
Unit tests for Sprint 2 nodes:
  - verify_steps.py   (Task 1.2 — Step Verification After Decomposition)
  - validate_answer.py (Task 2.1 — Rich Answer Validation)
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
from app.services.socratic.verify_steps import (
    _safe_eval_arithmetic,
    verify_step_schema,
    verify_math_convergence,
    verify_no_answer_leakage,
    verify_readability,
    verify_steps,
    verify_steps_node,
)
# pyrefly: ignore [missing-import]
from app.services.socratic.validate_answer import (
    validate_student_answer,
    VALIDATION_CORRECT,
    VALIDATION_PARTIAL,
    VALIDATION_INCORRECT,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Step Verification Tests (Task 1.2)
# ─────────────────────────────────────────────────────────────────────────────

class TestStepVerification:

    def test_safe_eval_arithmetic_basic(self):
        assert _safe_eval_arithmetic("12 + 15") == 27.0
        assert _safe_eval_arithmetic("8 * 7") == 56.0
        assert _safe_eval_arithmetic("24 / 4") == 6.0
        assert _safe_eval_arithmetic("15 - 9") == 6.0

    def test_safe_eval_arithmetic_unicode_operators(self):
        assert _safe_eval_arithmetic("6 × 7") == 42.0
        assert _safe_eval_arithmetic("20 ÷ 5") == 4.0

    def test_safe_eval_rejects_unsafe_code(self):
        assert _safe_eval_arithmetic("__import__('os').system('dir')") is None
        assert _safe_eval_arithmetic("open('file.txt')") is None

    def test_schema_valid_steps(self):
        steps = [
            {"step_number": 1, "mission": "Count the apples in row 1.", "expected_answer": "4", "hints": ["Look at row 1"]},
            {"step_number": 2, "mission": "Count the apples in row 2.", "expected_answer": "5", "hints": ["Look at row 2"]},
            {"step_number": 3, "mission": "Add row 1 and row 2 together.", "expected_answer": "9", "hints": ["4 + 5 = ?"]},
        ]
        is_valid, issues = verify_step_schema(steps)
        assert is_valid is True
        assert len(issues) == 0

    def test_schema_rejects_single_step(self):
        steps = [{"step_number": 1, "mission": "Solve it all.", "expected_answer": "42"}]
        is_valid, issues = verify_step_schema(steps)
        assert is_valid is False
        assert any("Too few steps" in issue for issue in issues)

    def test_schema_rejects_too_many_steps(self):
        steps = [{"step_number": i, "mission": f"Mini step {i}", "expected_answer": str(i)} for i in range(1, 8)]
        is_valid, issues = verify_step_schema(steps)
        assert is_valid is False
        assert any("Too many steps" in issue for issue in issues)

    def test_schema_rejects_empty_expected_answer(self):
        steps = [
            {"step_number": 1, "mission": "Step 1 prompt", "expected_answer": ""},
            {"step_number": 2, "mission": "Step 2 prompt", "expected_answer": "5"},
        ]
        is_valid, issues = verify_step_schema(steps)
        assert is_valid is False
        assert any("missing an expected answer" in issue for issue in issues)

    def test_math_convergence_valid(self):
        steps = [
            {"step_number": 1, "mission": "Identify numbers", "expected_answer": "12 and 15"},
            {"step_number": 2, "mission": "Add them together", "expected_answer": "27"},
        ]
        is_valid, issues = verify_math_convergence("What is 12 + 15?", steps)
        assert is_valid is True
        assert len(issues) == 0

    def test_math_convergence_catches_hallucination(self):
        steps = [
            {"step_number": 1, "mission": "Identify numbers", "expected_answer": "12 and 15"},
            {"step_number": 2, "mission": "Add them together", "expected_answer": "26"},  # Wrong: 12 + 15 = 27
        ]
        is_valid, issues = verify_math_convergence("What is 12 + 15?", steps)
        assert is_valid is False
        assert any("Math mismatch" in issue for issue in issues)

    def test_answer_leakage_detected(self):
        steps = [
            {"step_number": 1, "mission": "Step 1", "clue": "The answer is photosynthesis so keep going.", "expected_answer": "sunlight"},
            {"step_number": 2, "mission": "Step 2", "expected_answer": "photosynthesis"},
        ]
        is_valid, issues = verify_no_answer_leakage(steps)
        assert is_valid is False
        assert any("directly leaks the final answer" in issue for issue in issues)

    def test_no_answer_leakage_on_clean_steps(self):
        steps = [
            {"step_number": 1, "mission": "Notice the leaves collecting sunlight.", "clue": "Plants need light energy.", "expected_answer": "sunlight"},
            {"step_number": 2, "mission": "What is this food-making process called?", "expected_answer": "photosynthesis"},
        ]
        is_valid, issues = verify_no_answer_leakage(steps)
        assert is_valid is True
        assert len(issues) == 0

    def test_readability_flags_overly_complex_text(self):
        steps = [
            {
                "step_number": 1,
                "mission": "Electrocardiographically conceptualize perpendicular phosphorescence through compartmentalization.",
                "expected_answer": "yes",
            },
            {
                "step_number": 2,
                "mission": "Supercalifragilisticexpialidocious interdenominational disproportionateness.",
                "expected_answer": "no",
            },
        ]
        is_valid, issues = verify_readability(steps)
        assert is_valid is False
        assert any("Vocabulary too complex" in issue for issue in issues)

    def test_verify_steps_node_integration(self):
        state = {
            "problem_text": "What is 8 + 7?",
            "subject": "math",
            "step_widget": {
                "steps": [
                    {"step_number": 1, "mission": "Break 7 into 2 and 5.", "expected_answer": "2 and 5", "hints": ["8 + 2 = 10"]},
                    {"step_number": 2, "mission": "Now add 10 + 5.", "expected_answer": "15", "hints": ["Count on from 10"]},
                ]
            }
        }
        updates = verify_steps_node(state)
        assert updates["steps_verified"] is True
        assert len(updates["verification_issues"]) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Rich Answer Validation Tests (Task 2.1)
# ─────────────────────────────────────────────────────────────────────────────

class TestRichAnswerValidation:

    def test_exact_number_match(self):
        res = validate_student_answer("15", "15")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True
        assert res.is_partial is False

    def test_khmer_digits_match(self):
        res = validate_student_answer("១៥", "15")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_fraction_and_decimal_equivalence(self):
        res = validate_student_answer("0.5", "1/2")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_percentage_equivalence(self):
        res = validate_student_answer("50%", "0.5")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_word_number_match(self):
        res = validate_student_answer("half", "0.5")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_khmer_word_number_match(self):
        res = validate_student_answer("ប្រាំ", "5")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_unit_stripping_correct(self):
        res = validate_student_answer("15 cm", "15")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_unit_mismatch_gives_partial(self):
        res = validate_student_answer("15 m", "15 cm")
        assert res.outcome == VALIDATION_PARTIAL
        assert res.is_partial is True
        assert res.unit_mismatch is True
        assert "units" in res.feedback_eng.lower()

    def test_near_miss_off_by_one(self):
        # 14 when expected is 15 - within +/- 1 proximity tolerance
        res = validate_student_answer("14", "15")
        assert res.outcome == VALIDATION_PARTIAL
        assert res.is_partial is True
        assert res.numeric_diff == 1.0
        assert "very close" in res.feedback_eng.lower()

    def test_near_miss_off_by_two(self):
        # 13 when expected is 15 - beyond +/- 1 tolerance, treated as standard incorrect
        res = validate_student_answer("13", "15")
        assert res.outcome == VALIDATION_INCORRECT
        assert res.is_correct is False
        assert res.is_partial is False

    def test_far_off_is_incorrect(self):
        res = validate_student_answer("99", "15")
        assert res.outcome == VALIDATION_INCORRECT
        assert res.is_correct is False
        assert res.is_partial is False

    def test_science_exact_synonym(self):
        res = validate_student_answer("water turns into gas", "evaporation", subject="science")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_science_partial_concept(self):
        # Student observes "steam" when expected is full evaporation
        res = validate_student_answer("steam", "evaporation", subject="science")
        assert res.outcome == VALIDATION_PARTIAL
        assert res.is_partial is True
        assert "steam" in res.feedback_eng.lower()

    def test_affirmative_khmer_english_cross(self):
        res = validate_student_answer("បាទ", "yes")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

    def test_negative_khmer_english_cross(self):
        res = validate_student_answer("គ្មាន", "no")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True
