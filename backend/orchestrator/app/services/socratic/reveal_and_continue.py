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
    Uses the step mission to detect subject (math/science) and builds
    a safe parallel example that doesn't expose the actual answer.
    """
    lower = (mission + " " + clue).lower()
    numbers = [int(n) for n in re.findall(r"\b(\d+)\b", mission)]

    # Math — addition
    if any(w in lower for w in ["+", "plus", "add", "total", "altogether", "sum"]) and len(numbers) >= 2:
        a, b = numbers[0], numbers[1]
        # Use different numbers (offset by small prime)
        sa, sb = a + 3, b + 2
        return (
            f"📖 **Worked Example (similar problem):**\n"
            f"If you had **{sa} 🍎 apples** and got **{sb} 🍎 more**, how many in total?\n\n"
            f"  {sa} + {sb} = **{sa + sb}** ✅\n\n"
            f"Now try the same steps on your problem!"
        )

    # Math — subtraction
    if any(w in lower for w in ["-", "minus", "subtract", "left", "remain", "gave", "ate"]) and len(numbers) >= 2:
        a, b = numbers[0], numbers[1]
        sa, sb = a + 4, b + 1
        return (
            f"📖 **Worked Example (similar problem):**\n"
            f"If there were **{sa} 🍊 oranges** and you ate **{sb}**, how many are left?\n\n"
            f"  {sa} − {sb} = **{sa - sb}** ✅\n\n"
            f"Use the same take-away thinking on your problem!"
        )

    # Science — classification / yes-no / feature
    if any(w in lower for w in ["vertebrate", "invertebrate", "backbone", "feature", "classify"]):
        return (
            f"📖 **Worked Example:**\n"
            f"Is a **fish** a vertebrate or invertebrate?\n\n"
            f"👉 A fish **has a backbone** → it is a **Vertebrate** ✅\n\n"
            f"Now check whether the animal in your problem has a backbone!"
        )

    # Science — photosynthesis / plants
    if any(w in lower for w in ["plant", "sunlight", "photosynthesis", "leaf", "roots"]):
        return (
            f"📖 **Worked Example:**\n"
            f"What does a **cactus** need to make its own food?\n\n"
            f"👉 All plants need **Sunlight ☀️ + Water 💧** → **Photosynthesis** ✅\n\n"
            f"Think about what the plant in your problem needs!"
        )

    # Science — states of matter
    if any(w in lower for w in ["evapor", "melt", "boil", "solid", "liquid", "gas", "state"]):
        return (
            f"📖 **Worked Example:**\n"
            f"When **butter** is left in a hot pan, what happens?\n\n"
            f"👉 Solid butter → heats up → becomes **liquid** (melting) ✅\n\n"
            f"Think about what state change is happening in your problem!"
        )

    # Generic fallback
    return (
        f"📖 **Worked Example:**\n"
        f"Here is how to approach a similar question:\n"
        f"1. Re-read the mission carefully.\n"
        f"2. Find the key fact or number.\n"
        f"3. Apply the operation or concept from the clue: _{clue}_\n\n"
        f"Now apply the same steps to your problem!"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Reveal & Continue Message Builder
# ─────────────────────────────────────────────────────────────────────────────

_REVEAL_INTRO_MESSAGES = [
    "You gave it your best shot — let's look at this one together! 🌟",
    "Great effort! Sometimes a worked example helps most. Let's see it! 📚",
    "Three tries is real perseverance! Let me show you how to approach this. 💪",
]

_TAKE_A_BREAK_MESSAGE = (
    "🌈 You've been working really hard! Take a short break — stretch, "
    "drink some water, and come back fresh. Your progress is saved! ☕\n\n"
    "Tap **Resume** when you're ready to continue. You're doing great! 🦁"
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
        f"✅ **The answer to Step {step_number} is: `{expected_answer}`**\n\n"
        f"Don't worry — every mistake helps you learn. "
        f"Onto the next step! 🚀"
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
            "feedback_message": "Great effort! Let's try a new problem. 🌟",
            "is_deflected": False,
        }

    active_step = widget.get_active_step()
    if not active_step:
        return {
            "feedback_message": "🎉 You've completed all steps! Amazing work!",
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
    }

    if not has_more:
        updates["is_problem_complete"] = True
        updates["is_problem_solved"] = True
        updates["feedback_message"] = (
            reveal_msg + "\n\n🎉 **You've completed all steps!** "
            "Amazing perseverance — keep it up! ⭐"
        )
    else:
        next_step = widget.get_active_step()
        updates["is_problem_complete"] = False
        updates["is_problem_solved"] = False
        if next_step:
            updates["feedback_message"] = (
                reveal_msg + f"\n\n➡️ **Moving on to Step {next_step.step_number}: "
                f"{next_step.title}**"
            )

    return updates
