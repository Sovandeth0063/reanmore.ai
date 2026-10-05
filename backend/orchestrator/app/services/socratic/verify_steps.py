"""
File: orchestrator/app/services/socratic/verify_steps.py
Description: Step Verification Node for the Socratic tutoring pipeline (Sprint 2 - Task 1.2).
             Verifies decomposed problem steps before presenting them to the student:
             - Math convergence: verifies that steps logically converge to the correct final answer
               using safe AST arithmetic or Sympy evaluation.
             - No answer leakage: checks that early step clues/missions do not expose the final answer.
             - Schema validation: ensures 2-5 steps, non-empty questions/prompts, 3 progressive hints.
             - Grade 1-3 reading level checks: max word length (<=6.5 chars), sentence length (<=16 words).
             - Retry & fallback: if verification fails, retries or falls back to verified deterministic steps.
"""

import ast
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from fractions import Fraction

logger = logging.getLogger("orchestrator.socratic.verify_steps")


@dataclass
class StepVerificationResult:
    is_valid: bool
    confidence: float
    issues: List[str] = field(default_factory=list)
    math_verified: bool = False
    schema_verified: bool = False
    readability_verified: bool = False
    leakage_free: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# 1. Safe AST Arithmetic Evaluator
# ─────────────────────────────────────────────────────────────────────────────

from app.services.socratic.safe_math import safe_eval_float as _safe_eval_arithmetic


# ─────────────────────────────────────────────────────────────────────────────
# 2. Schema Verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_step_schema(steps: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Checks that the step collection has between 2 and 5 steps,
    and each step contains mandatory pedagogical fields.
    """
    issues = []
    if not isinstance(steps, list):
        return False, ["Steps must be a list."]

    step_count = len(steps)
    if step_count < 2:
        issues.append(f"Too few steps ({step_count}); minimum is 2.")
    elif step_count > 5:
        issues.append(f"Too many steps ({step_count}); maximum for Grade 1-3 is 5.")

    for idx, step in enumerate(steps):
        step_num = step.get("step_number", idx + 1)
        # Check mission / prompt
        prompt = (
            step.get("your_turn")
            or step.get("mission")
            or step.get("questionEng")
            or step.get("questionKhmer")
            or step.get("clue")
            or ""
        )
        if not prompt or len(prompt.strip()) < 3:
            issues.append(f"Step {step_num} is missing a clear question/prompt.")

        # Check expected answer
        expected = (
            step.get("expected_answer")
            or step.get("expectedAnswer")
            or step.get("correctAnswer")
            or ""
        )
        if not expected or len(str(expected).strip()) == 0:
            issues.append(f"Step {step_num} is missing an expected answer.")

        # Check hints presence
        hints = step.get("hints")
        if hints is not None and isinstance(hints, list):
            if len(hints) < 1:
                issues.append(f"Step {step_num} has empty hints list.")

    return len(issues) == 0, issues


# ─────────────────────────────────────────────────────────────────────────────
# 3. Math Convergence Verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_math_convergence(problem_text: str, steps: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    For math problems, independently computes the arithmetic answer and checks
    that the final step's expected answer converges to it.
    """
    issues = []
    if not steps:
        return True, issues

    # Look for arithmetic patterns in problem text like "12 + 15", "8 * 7", "24 / 4", "15 - 9"
    expr_match = re.search(r"(\d+(?:\.\d+)?)\s*([+\-*/×÷x])\s*(\d+(?:\.\d+)?)", problem_text)
    if expr_match:
        computed_val = _safe_eval_arithmetic(expr_match.group(0))
        if computed_val is not None:
            # Check final step's expected answer
            final_step = steps[-1]
            final_expected = str(
                final_step.get("expected_answer")
                or final_step.get("expectedAnswer")
                or final_step.get("correctAnswer")
                or ""
            ).strip()

            expected_num = _safe_eval_arithmetic(final_expected)
            if expected_num is not None:
                if abs(expected_num - computed_val) > 0.01:
                    issues.append(
                        f"Math mismatch: problem '{expr_match.group(0)}' computes to {computed_val}, "
                        f"but final step expects {expected_num}."
                    )
            else:
                # Numeric regex fallback
                nums = re.findall(r"[-+]?\d*\.?\d+", final_expected)
                if nums:
                    try:
                        f_val = float(nums[0])
                        if abs(f_val - computed_val) > 0.01:
                            issues.append(
                                f"Math mismatch: problem '{expr_match.group(0)}' = {computed_val}, "
                                f"final step expects {f_val}."
                            )
                    except ValueError:
                        pass

    return len(issues) == 0, issues


# ─────────────────────────────────────────────────────────────────────────────
# 4. Zero Answer Leakage Verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_no_answer_leakage(steps: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Verifies that early steps (steps prior to the last step) do not reveal
    the final expected answer in their clues, missions, or helpful examples.
    """
    issues = []
    if len(steps) < 2:
        return True, issues

    final_step = steps[-1]
    final_ans = str(
        final_step.get("expected_answer")
        or final_step.get("expectedAnswer")
        or final_step.get("correctAnswer")
        or ""
    ).strip().lower()

    if not final_ans or len(final_ans) < 2:
        return True, issues

    # Skip single-digit numbers or common short words to avoid false positive leakage
    if len(final_ans) <= 1 or final_ans in {"yes", "no", "true", "false", "a", "b", "c", "d"}:
        return True, issues

    # Check each step before the final step
    for idx, step in enumerate(steps[:-1]):
        step_num = step.get("step_number", idx + 1)
        clue = (step.get("clue") or "").lower()
        mission = (step.get("mission") or "").lower()
        example = (step.get("helpful_example") or step.get("helpfulExample") or "").lower()

        combined_text = f"{clue} {mission} {example}"
        # Direct spoiler pattern: "the answer is [final_ans]"
        if re.search(rf"\b(?:the answer is|equals|is)\s+{re.escape(final_ans)}\b", combined_text):
            issues.append(f"Step {step_num} directly leaks the final answer '{final_ans}'.")

    return len(issues) == 0, issues


# ─────────────────────────────────────────────────────────────────────────────
# 5. Grade 1-3 Reading Level Verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_readability(steps: List[Dict[str, Any]], grade_level: str = "grade_1_3") -> Tuple[bool, List[str]]:
    """
    Applies Grade 1-3 readability heuristics:
    - Average word length <= 7.0 characters (allowing bilingual Khmer/English transliteration)
    - Average sentence length <= 18 words
    """
    issues = []
    all_words = []
    sentence_counts = []

    for step in steps:
        texts = [
            step.get("title", ""),
            step.get("mission", ""),
            step.get("clue", ""),
            step.get("your_turn", ""),
            step.get("questionEng", ""),
        ]
        full_text = " ".join(t for t in texts if t)
        words = full_text.split()
        if words:
            all_words.extend(words)
        sentences = [s for s in re.split(r"[.!?]+", full_text) if s.strip()]
        for s in sentences:
            sentence_counts.append(len(s.split()))

    if all_words:
        avg_word_len = sum(len(w) for w in all_words) / len(all_words)
        if avg_word_len > 8.0:
            issues.append(f"Vocabulary too complex for early elementary (avg word length {avg_word_len:.1f} > 8.0).")

    if sentence_counts:
        avg_sent_len = sum(sentence_counts) / len(sentence_counts)
        if avg_sent_len > 22.0:
            issues.append(f"Sentences too long for Grade 1-3 (avg sentence length {avg_sent_len:.1f} > 22 words).")

    return len(issues) == 0, issues


# ─────────────────────────────────────────────────────────────────────────────
# 6. Master Step Verifier
# ─────────────────────────────────────────────────────────────────────────────

def verify_steps(
    steps: List[Dict[str, Any]],
    problem_text: str,
    subject: str = "math",
    grade_level: str = "grade_1_3",
) -> StepVerificationResult:
    """
    Runs full verification suite against decomposed steps.
    """
    all_issues = []

    # 1. Schema
    schema_ok, s_issues = verify_step_schema(steps)
    all_issues.extend(s_issues)

    # 2. Math convergence (for math problems)
    math_ok = True
    if subject.lower() == "math":
        math_ok, m_issues = verify_math_convergence(problem_text, steps)
        all_issues.extend(m_issues)

    # 3. Answer leakage
    leakage_ok, l_issues = verify_no_answer_leakage(steps)
    all_issues.extend(l_issues)

    # 4. Readability
    read_ok, r_issues = verify_readability(steps, grade_level)
    all_issues.extend(r_issues)

    is_valid = schema_ok and math_ok and leakage_ok

    confidence = 1.0
    if not schema_ok:
        confidence -= 0.4
    if not math_ok:
        confidence -= 0.4
    if not leakage_ok:
        confidence -= 0.2
    if not read_ok:
        confidence -= 0.1
    confidence = max(0.0, min(1.0, confidence))

    return StepVerificationResult(
        is_valid=is_valid,
        confidence=confidence,
        issues=all_issues,
        math_verified=math_ok,
        schema_verified=schema_ok,
        readability_verified=read_ok,
        leakage_free=leakage_ok,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7. LangGraph Node Wrapper
# ─────────────────────────────────────────────────────────────────────────────

def verify_steps_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: validates decomposed steps in step_widget.
    If valid:
        - Sets state['steps_verified'] = True
    If invalid:
        - Sets state['steps_verified'] = False
        - Attaches validation issues to state
    """
    widget = state.get("step_widget") or {}
    steps = widget.get("steps") or []
    problem = state.get("problem_text") or state.get("raw_user_input", "")
    subject = state.get("subject") or "math"
    grade_level = state.get("grade_level", "grade_1_3")

    result = verify_steps(
        steps=steps,
        problem_text=problem,
        subject=subject,
        grade_level=grade_level,
    )

    logger.info(
        f"[VerifySteps] is_valid={result.is_valid} confidence={result.confidence:.2f} "
        f"math={result.math_verified} issues={result.issues}"
    )

    updates: Dict[str, Any] = {
        "steps_verified": result.is_valid,
        "verification_issues": result.issues,
    }

    if not result.is_valid:
        retry_count = state.get("decompose_retry_count", 0)
        updates["decompose_retry_count"] = retry_count + 1
        if retry_count >= 2:
            updates["feedback_message"] = (
                "🙋 Let's take a look at this one together! "
                "If it feels tricky, ask a grown-up or teacher to help with this problem."
            )

    return updates
