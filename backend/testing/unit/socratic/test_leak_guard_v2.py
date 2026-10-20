"""
File: backend/testing/unit/socratic/test_leak_guard_v2.py
Description: Unit tests for Leak Guard v2:
             - Given Operands Allowlist (permits problem numbers without false positives)
             - 6-Token Disclosure Window (flags 'the answer is X')
             - Structural Example Masking (exempts verified parallel worked demonstrations)
             - VisualSpec Security Scanner integration
             Implements Architecture v2.1 Section 10.1 & Phase 1C.
"""

import pytest
from fractions import Fraction
from app.services.guardrails.leak_guard import (
    check_tutor_response_leak,
    scan_visual_spec,
    SAFE_CLUE_FALLBACK_ENG,
    SAFE_PRAISE_FALLBACK_ENG
)
from app.services.visuals.schema import VisualSpec, VisualType, VisualMode


def test_given_operands_allowlist_permits_problem_restatement():
    """
    Given Operands Allowlist: Numbers explicitly in the student's problem text
    (e.g. 12 and 4 in 'Leo had 12 apples and ate 4') must NOT be falsely quarantined
    when the tutor pedagogically restates them, even if Step 1 asks for one of them.
    """
    problem = "Leo had 12 apples and ate 4. How many apples are left?"
    tutor_reply = "Leo started with 12 apples, and then 4 were eaten. Let's find how many are left!"
    target_answer = "12"

    is_leak, final_reply, reason = check_tutor_response_leak(
        tutor_reply=tutor_reply,
        target_answer=target_answer,
        problem_text=problem,
        is_step_solved=False
    )
    assert is_leak is False, f"Falsely blocked given operand: {reason}"
    assert "Leo started with 12 apples" in final_reply


def test_given_operands_blocks_direct_disclosure():
    """
    If an operand from the problem text is disclosed within an explicit answer
    disclosure window ("the answer is 12"), it must still be quarantined!
    """
    problem = "Leo had 12 apples and ate 4. How many apples are left?"
    tutor_reply = "Great question! The answer is 12."
    target_answer = "12"

    is_leak, final_reply, reason = check_tutor_response_leak(
        tutor_reply=tutor_reply,
        target_answer=target_answer,
        problem_text=problem,
        is_step_solved=False
    )
    assert is_leak is True
    assert final_reply == SAFE_CLUE_FALLBACK_ENG


def test_unsolved_target_not_in_problem_is_always_blocked():
    """
    If a number is NOT in the student's problem statement (e.g. 8 is the unsolved
    target for 12 - 4), ANY appearance in tutor reply must be caught and blocked.
    """
    problem = "Leo had 12 apples and ate 4. How many apples are left?"
    tutor_reply = "There are 8 apples remaining."
    target_answer = "8"

    is_leak, final_reply, reason = check_tutor_response_leak(
        tutor_reply=tutor_reply,
        target_answer=target_answer,
        problem_text=problem,
        is_step_solved=False
    )
    assert is_leak is True
    assert "numeric_answer_leak_detected" in reason


def test_structural_example_masking_permits_parallel_expressions():
    """
    Equations inside a verified distinct parallel example (e.g. 15 - 6 = 9)
    must not trigger false positive leak interceptions.
    """
    problem = "Leo had 12 apples and ate 4. How many apples are left?"
    tutor_reply = (
        "🌟 **Our Mission:** Subtract the eaten apples.\n\n"
        "💡 **Clue:** Subtracting gives what is left.\n\n"
        "🍎 **Helpful Picture / Example:**\n"
        "> For Sophea's problem: 15 - 6 = 9 mangoes left.\n\n"
        "👉 **Your Turn:**\n"
        "What is 12 - 4?"
    )
    target_answer = "8"

    is_leak, final_reply, reason = check_tutor_response_leak(
        tutor_reply=tutor_reply,
        target_answer=target_answer,
        problem_text=problem,
        is_step_solved=False
    )
    assert is_leak is False, f"Falsely blocked parallel example: {reason}"
    assert "15 - 6 = 9" in final_reply


def test_structural_example_catches_target_collision():
    """
    If a parallel example inadvertently contains the student's actual target answer (8),
    Leak Guard v2 must NOT mask it and must catch the collision.
    """
    problem = "Leo had 12 apples and ate 4. How many apples are left?"
    tutor_reply = (
        "🍎 **Helpful Picture / Example:**\n"
        "> Notice that 13 - 5 = 8!\n\n"
        "👉 **Your Turn:**"
    )
    target_answer = "8"

    is_leak, final_reply, reason = check_tutor_response_leak(
        tutor_reply=tutor_reply,
        target_answer=target_answer,
        problem_text=problem,
        is_step_solved=False
    )
    assert is_leak is True


def test_scan_visual_spec_clean_and_leak():
    """
    Tests scan_visual_spec integration for clean vs leaking visual payloads.
    """
    clean_spec = {
        "schema_version": 1,
        "type": "ten_frame",
        "mode": "current",
        "params": {"frames": [{"filled": 8}, {"filled": 2}]},
        "labels": ["8 apples"],
        "alt_text": "Ten frame with 8 apples."
    }
    is_leak, sanitized, _ = scan_visual_spec(clean_spec, target_answer="14")
    assert is_leak is False

    # Leaking spec: params contains target answer 14
    leaking_spec = {
        "schema_version": 1,
        "type": "number_line",
        "mode": "current",
        "params": {"start": 10, "hops": [{"from": 10, "to": 14}]},
        "labels": ["Hop to 14"],
        "alt_text": "Number line hopping to 14."
    }
    is_leak_bad, sanitized_bad, reason = scan_visual_spec(leaking_spec, target_answer="14")
    assert is_leak_bad is True
    assert "visual_param_leak_detected" in reason
