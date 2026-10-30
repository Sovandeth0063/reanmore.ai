"""
File: orchestrator/app/services/socratic/reveal_and_continue.py
Description: Hint Level 3 Exit Node — "Reveal & Continue"
             Triggered after 3 consecutive wrong answers for the same step.
             Shows a worked example of a SIMILAR (not identical) problem,
             then reveals the correct answer with a brief explanation.
             Updates mastery records: marks step as "needed_reveal".

             Also contains: frustration detection helpers used by the graph.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("orchestrator.socratic.reveal_and_continue")


# ─────────────────────────────────────────────────────────────────────────────
# Frustration Score Calculator
# ─────────────────────────────────────────────────────────────────────────────

def compute_frustration_score(
    attempt_history: List[Dict[str, Any]],
    response_time_ms: Optional[float] = None,
    idle_seconds: Optional[float] = None,
) -> float:
    """
    Computes a 0.0–1.0 frustration score from attempt history and timing signals.

    Scoring:
        +0.2 per consecutive wrong answer in the last 5 attempts (max +0.6)
        +0.3 if response_time_ms < 2500ms (fast guess / not thinking)
        +0.2 if idle_seconds > 90 (stuck, not typing)
        Capped at 1.0.
    """
    score = 0.0
    recent = attempt_history[-5:] if attempt_history else []

    # Count consecutive wrong at the tail
    consecutive_wrong = 0
    for attempt in reversed(recent):
        if not attempt.get("is_correct", True):
            consecutive_wrong += 1
        else:
            break
    score += min(consecutive_wrong * 0.2, 0.6)

    # Fast guess signal
    if response_time_ms is not None and response_time_ms < 2500:
        score += 0.3

    # Idle signal
    if idle_seconds is not None and idle_seconds > 90:
        score += 0.2

    return min(score, 1.0)


def should_offer_break(frustration_score: float, threshold: float = 0.80) -> bool:
    """Returns True if the frustration score exceeds the break threshold."""
    return frustration_score >= threshold


# ─────────────────────────────────────────────────────────────────────────────
# Isomorphic "Similar Problem" Example Generator
# ─────────────────────────────────────────────────────────────────────────────

def _build_worked_example(
    mission: str,
    expected_answer: str,
    clue: str,
) -> str:
    """
    Generates a worked example for a SIMILAR problem, not the exact one.
    Content is produced by the LLM prompt for this step; no per-topic answer
    bank is embedded in the code. If the model is unavailable, a generic
    instruction is returned instead of a canned science example.
    """
    try:
        from app.services.socratic.prompts.controller import controller

        prompt = controller.get_parallel_example_prompt(
            f"{mission}\n{clue}"
        )
        raw = controller._call_gemini_llm(prompt)
        if raw:
            return f" **Worked Example (similar problem):**\n{raw.strip()}\n\nNow try the same steps on your problem!"
    except Exception as e:
        logger.warning(f"Worked-example generation failed: {e}")

    # Generic fallback: contains no subject-specific answer.
    return (
        f" **Worked Example (similar problem):**\n"
        f"Try a smaller version of this question using different numbers or objects, "
        f"then apply the same steps to your problem.\n\n"
        f"Clue to reuse: _{clue}_\n\n"
        f"Now apply the same thinking here!"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Reveal & Continue Message Builder
# ─────────────────────────────────────────────────────────────────────────────

_REVEAL_INTRO_MESSAGES = [
    "You gave it your best shot — let's look at this one together! ",
    "Great effort! Sometimes a worked example helps most. Let's see it! ",
    "Three tries is real perseverance! Let me show you how to approach this. ",
]

_TAKE_A_BREAK_MESSAGE = (
    " You've been working really hard! Take a short break — stretch, "
    "drink some water, and come back fresh. Your progress is saved! \n\n"
    "Tap **Resume** when you're ready to continue. You're doing great! "
)


def build_reveal_message(
    step_number: int,
    mission: str,
    expected_answer: str,
    clue: str,
    attempt_history: List[Dict[str, Any]],
    grade_level: str = "grade_1_3",
) -> str:
    """
    Builds the full 'reveal and continue' message shown after 3 wrong answers.
    Includes a worked example of a similar problem and then the actual answer.
    """
    intro = _REVEAL_INTRO_MESSAGES[step_number % len(_REVEAL_INTRO_MESSAGES)]
    worked = _build_worked_example(mission, expected_answer, clue)

    msg = (
        f"{intro}\n\n"
        f"{worked}\n\n"
        f"---\n\n"
        f" **The answer to Step {step_number} is: `{expected_answer}`**\n\n"
        f"Don't worry — every mistake helps you learn. "
        f"Onto the next step! "
    )
    return msg


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Node
# ─────────────────────────────────────────────────────────────────────────────

def reveal_and_continue_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: triggered when hint_level reaches 3 and answer is still wrong.

    Behaviour:
        1. Build a worked example + answer reveal message.
        2. Advance the widget to the next step (marking current as completed).
        3. Update mastery record: 'needed_reveal' += 1 for this step's concept.
        4. Check frustration score; if >= 0.8, set take_a_break=True.

    State reads:
        - step_widget, current_hint_tier, attempt_history,
          response_time_ms (optional), idle_seconds (optional)

    State writes:
        - feedback_message, step_widget, current_step_index,
          is_problem_complete, current_hint_tier, mastery, take_a_break
    """
    from app.services.socratic.graph import _get_widget_from_state

    widget = _get_widget_from_state(state)
    if not widget:
        return {
            "feedback_message": "Great effort! Let's try a new problem. ",
            "is_deflected": False,
        }

    active_step = widget.get_active_step()
    if not active_step:
        return {
            "feedback_message": " You've completed all steps! Amazing work!",
            "is_problem_complete": True,
            "is_problem_solved": True,
        }

    attempt_history: List[Dict[str, Any]] = list(state.get("attempt_history", []))
    response_time_ms: Optional[float] = state.get("response_time_ms")
    idle_seconds: Optional[float] = state.get("idle_seconds")

    # 1. Compute frustration
    frustration = compute_frustration_score(
        attempt_history=attempt_history,
        response_time_ms=response_time_ms,
        idle_seconds=idle_seconds,
    )
    take_a_break = should_offer_break(frustration)

    if take_a_break:
        logger.info(
            f"[RevealAndContinue] Frustration score {frustration:.2f} >= 0.8. "
            "Offering break."
        )
        return {
            "feedback_message": _TAKE_A_BREAK_MESSAGE,
            "take_a_break": True,
            "frustration_score": frustration,
            "step_widget": widget.model_dump(),
            "current_step_index": widget.current_step_index,
        }

    # 2. Build reveal message
    reveal_msg = build_reveal_message(
        step_number=active_step.step_number,
        mission=active_step.mission or active_step.title or "",
        expected_answer=active_step.expected_answer or "—",
        clue=active_step.clue or "",
        attempt_history=attempt_history,
        grade_level=state.get("grade_level", "grade_1_3"),
    )

    # 3. Record in attempt history
    attempt_history.append({
        "step_number": active_step.step_number,
        "student_attempt": "[REVEALED]",
        "is_correct": False,
        "feedback": "Answer revealed after 3 wrong attempts.",
        "hints_used": 3,
        "was_revealed": True,
    })

    try:
        from app.services.telemetry.gap_recorder import log_gap_event
        log_gap_event(
            gap_type="learner",
            gap_code="REVEAL_TRIGGERED",
            severity=2,
            user_id=state.get("user_id"),
            session_id=state.get("session_id"),
            problem_id=state.get("problem_id"),
            grade_tier=state.get("grade_level", "grade_1_3"),
            subject=state.get("subject", "math"),
            step_index=active_step.step_number,
            details={
                "step_title": active_step.title,
                "concept": active_step.concept,
                "expected_answer": active_step.expected_answer,
                "frustration_score": frustration,
            }
        )
    except Exception as e:
        logger.debug(f"[RevealAndContinue] Gap log failed: {e}")

    # 4. Advance widget (mark step complete so pipeline can continue)
    active_step.student_answer = active_step.expected_answer  # record correct answer
    has_more = widget.advance_step(recorded_answer=active_step.expected_answer)

    # 5. Update mastery
    mastery: Dict[str, Any] = dict(state.get("mastery", {}))
    concept_key = (active_step.concept or active_step.title or f"step_{active_step.step_number}").lower()
    if concept_key not in mastery:
        mastery[concept_key] = {"correct_first_try": 0, "needed_hints": 0, "needed_reveal": 0}
    mastery[concept_key]["needed_reveal"] = mastery[concept_key].get("needed_reveal", 0) + 1

    updates: Dict[str, Any] = {
        "feedback_message": reveal_msg,
        "step_widget": widget.model_dump(),
        "current_step_index": widget.current_step_index,
        "current_hint_tier": 0,
        "active_hint": None,
        "attempt_history": attempt_history,
        "mastery": mastery,
        "take_a_break": False,
        "frustration_score": frustration,
        "is_reveal_state": True,
    }

    if not has_more:
        updates["is_problem_complete"] = True
        updates["is_problem_solved"] = True
        updates["feedback_message"] = (
            reveal_msg + "\n\n **You've completed all steps!** "
            "Amazing perseverance — keep it up! ⭐"
        )
    else:
        next_step = widget.get_active_step()
        updates["is_problem_complete"] = False
        updates["is_problem_solved"] = False
        if next_step:
            updates["feedback_message"] = (
                reveal_msg + f"\n\n️ **Moving on to Step {next_step.step_number}: "
                f"{next_step.title}**"
            )

    return updates
