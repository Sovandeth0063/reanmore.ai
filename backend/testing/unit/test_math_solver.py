import os
import sys

from pytest import MonkeyPatch


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MATH_SERVICE = os.path.join(REPO_ROOT, "services", "math_service")
for path in (REPO_ROOT, MATH_SERVICE):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.solvers.algebra import decompose_arithmetic, solve_math_ai


def test_compound_expression_respects_operator_precedence():
    result = decompose_arithmetic("2 + 3 * 4")

    assert result["success"] is True
    assert result["solution"] == "14"


def test_fractional_division_is_not_truncated():
    result = decompose_arithmetic("5 / 2")

    assert result["success"] is True
    assert result["solution"] == "2.5"


def test_word_problem_division_preserves_fractional_result_without_api_key(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("app.solvers.algebra.GEMINI_API_KEY", "")

    result = solve_math_ai("5 cookies shared equally between 2 children", "grade_3_4")

    assert result["success"] is True
    assert result["solution"] == "2.5"