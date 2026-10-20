import os
import sys
import pytest


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


def test_word_to_num_and_khmer_number_equivalence():
    assert _is_answer_equivalent("eight", "8") is True
    assert _is_answer_equivalent("8 apples", "8") is True
    assert _is_answer_equivalent("មួយ", "1") is True
    assert _is_answer_equivalent("ប្រាំ", "5") is True
    assert _is_answer_equivalent("half", "0.5") is True
    assert _is_answer_equivalent("three quarters", "0.75") is True


def test_affirmative_and_negative_cross_language_equivalence():
    assert _is_answer_equivalent("yes", "true") is True
    assert _is_answer_equivalent("បាទ", "ចាស") is True
    assert _is_answer_equivalent("ត្រូវ", "yes") is True
    assert _is_answer_equivalent("no", "false") is True
    assert _is_answer_equivalent("ទេ", "no") is True


def test_science_equivalence_via_rubric():
    # Primary rubric concepts from validate_student_answer
    assert _is_answer_equivalent("liquid turns into gas", "evaporation") is True
    assert _is_answer_equivalent("រស្មីសំយោគ", "photosynthesis") is True
    assert _is_answer_equivalent("សត្វមានឆ្អឹងកង", "vertebrates") is True


@pytest.mark.asyncio
async def test_fast_validate_answer_endpoint_non_directional_near_miss():
    from app.api.endpoints import fast_validate_answer_endpoint, StepValidateRequest
    from app.core.tutoring_config import NEAR_MISS_FEEDBACK_ENG, NEAR_MISS_FEEDBACK_KHMER

    # 1. Exact match
    req_correct = StepValidateRequest(student_answer="8", expected_answer="8", language="en")
    res_correct = await fast_validate_answer_endpoint(req_correct)
    assert res_correct["is_correct"] is True
    assert res_correct["near_miss"] is False

    # 2. Near miss (+/- 1) strictly non-directional (no "1 away" or "count on 1 more")
    req_near = StepValidateRequest(student_answer="7", expected_answer="8", language="en")
    res_near = await fast_validate_answer_endpoint(req_near)
    assert res_near["is_correct"] is False
    assert res_near["near_miss"] is True
    assert res_near["feedback_eng"] == NEAR_MISS_FEEDBACK_ENG
    assert "1 away" not in res_near["feedback_eng"]
    assert "count on" not in res_near["feedback_eng"].lower()

    # 3. Khmer near miss strictly non-directional
    req_near_km = StepValidateRequest(student_answer="7", expected_answer="8", language="km")
    res_near_km = await fast_validate_answer_endpoint(req_near_km)
    assert res_near_km["is_correct"] is False
    assert res_near_km["near_miss"] is True
    assert res_near_km["feedback_khmer"] == NEAR_MISS_FEEDBACK_KHMER
    assert "១ ទៀត" not in res_near_km["feedback_khmer"]