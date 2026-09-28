import os
import sys


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ORCHESTRATOR = os.path.join(REPO_ROOT, "orchestrator")
for path in (REPO_ROOT, ORCHESTRATOR):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.services.socratic.graph import _is_answer_equivalent


def test_numeric_answer_does_not_match_a_larger_number():
    assert _is_answer_equivalent("10", "1") is False
    assert _is_answer_equivalent("21", "1") is False


def test_numeric_and_fraction_answers_are_equivalent():
    assert _is_answer_equivalent("2.5", "5/2") is True
    assert _is_answer_equivalent("២", "2") is True


def test_empty_or_missing_answers_are_not_equivalent():
    assert _is_answer_equivalent("", "1") is False
    assert _is_answer_equivalent("1", "") is False