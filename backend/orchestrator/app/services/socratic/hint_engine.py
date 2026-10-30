"""
File: orchestrator/app/services/socratic/hint_engine.py
Description: 3-Tier Progressive Hint Engine for elementary Socratic tutoring.
             Guarantees zero answer leakage across Nudge, Visual, and Micro-Breakdown tiers.
"""

import re
import logging
from typing import Optional, Dict, List, Any, Tuple
from app.services.socratic.card_schema import SocraticStep
from app.services.socratic.prompts.controller import SocraticPromptController

logger = logging.getLogger("orchestrator.socratic.hint_engine")


class HintEngine:
    """
    Manages progressive 3-tier hint generation for elementary students (Grades 1-6).
    Tier 1: Guiding Nudge (focus attention on key terms/starting values, no arithmetic)
    Tier 2: Visual Scaffold (emoji diagrams, cross-out illustrations)
    Tier 3: Micro-Breakdown (small bite-sized calculation sub-steps, no final answer)
    """

    def __init__(self, prompt_controller: Optional[SocraticPromptController] = None):
        self.prompt_controller = prompt_controller or SocraticPromptController()

    def escalate_hint(
        self,
        step: SocraticStep,
        prior_attempts: Optional[List[str]] = None,
        grade_level: str = "grade_1_3"
    ) -> Tuple[int, str]:
        """
        Advances the hint level for the step (capped at 3) and returns (new_level, hint_text).
        """
        prior_attempts = prior_attempts or []
        next_tier = min(step.current_hint_level + 1, 3)
        step.current_hint_level = next_tier

        # Use pre-computed hint if already cached in step.hints. Cached hints are
        # LLM-authored step content too, so they pass through the same zero-leak
        # guard as freshly generated hints.
        if next_tier <= len(step.hints) and step.hints[next_tier - 1]:
            hint_text = self._guard_hint(
                step.hints[next_tier - 1], step, next_tier
            )
            logger.info(f"[HintEngine] Used pre-computed hint tier {next_tier}")
        else:
            hint_text = self.generate_hint(
                step=step,
                tier=next_tier,
                prior_attempts=prior_attempts,
                grade_level=grade_level
            )
            # Cache it into step.hints
            while len(step.hints) < next_tier:
                step.hints.append("")
            step.hints[next_tier - 1] = hint_text

        logger.info(f"[HintEngine] Generated hint level {next_tier} for step {step.step_number}")

        if next_tier == 3:
            try:
                from app.services.telemetry.gap_recorder import log_gap_event
                log_gap_event(
                    gap_type="learner",
                    gap_code="HINT_ESCALATION",
                    severity=1,
                    grade_tier=grade_level,
                    step_index=step.step_number,
                    details={
                        "step_title": step.title,
                        "concept": step.concept,
                        "prior_attempts": prior_attempts,
                    }
                )
            except Exception as e:
                logger.debug(f"[HintEngine] Gap log failed: {e}")

        return next_tier, hint_text

    def generate_hint(
        self,
        step: SocraticStep,
        tier: int,
        prior_attempts: Optional[List[str]] = None,
        grade_level: str = "grade_1_3"
    ) -> str:
        """
        Generates a grade-appropriate hint for the target tier.
        Content comes exclusively from the LLM hint prompt; when the model is
        unavailable only a generic prompt built from this step's own fields is used.
        Enforces strict zero answer leakage: Tier 1-3 hints never contain the expected answer.
        """
        prior_attempts = prior_attempts or []
        attempts_str = ", ".join(prior_attempts) if prior_attempts else "None yet"

        # 1. LLM-generated hint (the prompt is the only content source)
        hint_text = ""
        try:
            prompt = self.prompt_controller.get_progressive_hint_prompt(
                step_mission=step.mission,
                your_turn_question=step.your_turn,
                hint_tier=tier,
                step_concept=step.concept or step.title,
                prior_attempts=attempts_str,
                grade_level=grade_level,
            )
            raw = self.prompt_controller._call_gemini_llm(prompt)
            if raw:
                hint_text = raw.strip()
        except Exception as e:
            logger.warning(f"Error generating LLM hint: {e}")

        # 2. Generic, content-derived fallback. It never contains a canned
        #    topic answer and is built only from this step's LLM-authored fields.
        if not hint_text:
            hint_text = self._generic_fallback_hint(step, tier)

        return self._guard_hint(hint_text, step, tier)

    def _guard_hint(self, hint_text: str, step: SocraticStep, tier: int) -> str:
        """Applies the zero-leakage invariant to a hint before it reaches the student.

        Only the student's own question is treated as given information. The step's
        mission, clue, and helpful example are *not* exempt: if the planner names the
        target concept there, a hint that repeats it would still give the answer away.
        """
        if not hint_text or not step.expected_answer:
            return hint_text

        from app.services.guardrails.leak_guard import check_tutor_response_leak

        is_leak, sanitized, reason = check_tutor_response_leak(
            tutor_reply=hint_text,
            target_answer=str(step.expected_answer),
            is_step_solved=False,
            is_reveal_state=False,
            current_hint_tier=tier,
            problem_text=step.your_turn or "",
        )
        if is_leak:
            logger.warning(
                f"[HintEngine] Leaked answer detected in hint tier {tier}: {reason}. "
                "Replacing with a content-free nudge."
            )
            return self._safe_generic_hint(tier)
        return sanitized

    @staticmethod
    def _safe_generic_hint(tier: int) -> str:
        """A content-free nudge safe for any subject and answer."""
        if tier <= 1:
            return "💡 Look back at the question: which detail stands out to you first?"
        if tier == 2:
            return "🎨 Picture the situation in your mind. What changes, and what stays the same?"
        return "🧩 Break the question into two small parts. What can you check first?"

    @staticmethod
    def _generic_fallback_hint(step: SocraticStep, tier: int) -> str:
        """Builds a hint from the step's own generated fields when the LLM is down."""
        clue = (step.clue or "").strip()
        example = (step.helpful_example or "").strip()
        focus = (step.your_turn or step.mission or "this step").strip()
        if tier <= 1:
            return f"👀 Re-read the clue: {clue}" if clue else f"👀 Focus on the question: {focus}"
        if tier == 2:
            return f"🎨 Picture this example: {example}" if example else f"🎨 Draw or picture the situation in '{focus}'."
        return f"🧩 Break it down: what is the first small thing you can check for '{focus}'?"
