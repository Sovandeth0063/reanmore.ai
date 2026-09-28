"""
File: orchestrator/app/services/socratic/card_schema.py
Description: Pydantic schemas and serialization models for the 4-Part Socratic Card
             and the interactive Stepper Widget payload (Grades 1-6).
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SocraticStep(BaseModel):
    """
    Represents an individual step in a Socratic learning problem.
    Adheres strictly to the 4-Part Step Card specification:
    1. 🌟 Our Mission
    2. 💡 Clue
    3. 🍎 Helpful Picture / Example (Isomorphic Parallel Example)
    4. 👉 Your Turn (One single question on the student's problem)
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    step_number: int = Field(..., description="1-indexed step number (e.g. 1, 2, 3)")
    title: str = Field(..., description="Short friendly title for the step")
    status: Literal["completed", "in_progress", "pending", "locked", "up_next"] = Field(
        default="pending",
        description="Status of this step in the student's workflow"
    )
    mission: str = Field(..., description="🌟 1 simple sentence defining what we are doing")
    clue: str = Field(..., description="💡 Grade-appropriate rule or concept")
    helpful_example: str = Field(
        ...,
        description="🍎 Isomorphic parallel example using visual emojis and concrete items"
    )
    your_turn: str = Field(
        ...,
        description="👉 Exactly ONE single question or prompt for the student to solve"
    )
    student_answer: Optional[str] = Field(
        default=None,
        description="Recorded student response for this step"
    )
    hints: List[str] = Field(
        default_factory=list,
        description="List of up to 3 progressive hints (Tier 1: Nudge, Tier 2: Visual, Tier 3: Worked)"
    )
    current_hint_level: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Active progressive hint tier (0 = none, 1-3 = progressive hint active)"
    )
    expected_answer: Optional[str] = Field(
        default=None,
        description="Ground truth or normalized target answer for evaluation"
    )
    concept: Optional[str] = Field(
        default=None,
        description="Underlying mathematical or scientific concept tag"
    )
    visual_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional visual scaffolding data for the step"
    )

    def to_markdown(self, active_hint: Optional[str] = None) -> str:
        """
        Renders the step into a beautifully formatted Markdown card with emojis.
        """
        lines = [
            f"🌟 **Our Mission:** {self.mission.strip()}",
            "",
            f"💡 **Clue:** {self.clue.strip()}",
            "",
            "🍎 **Helpful Picture / Example:**",
            f"> {self.helpful_example.strip()}",
            "",
            "👉 **Your Turn:**",
            f"{self.your_turn.strip()}"
        ]

        # Append hint if explicitly passed or active
        hint_to_show = active_hint
        if not hint_to_show and 0 < self.current_hint_level <= len(self.hints):
            hint_to_show = self.hints[self.current_hint_level - 1]

        if hint_to_show:
            lines.extend([
                "",
                f"💡 **Hint ({max(1, self.current_hint_level)}/3):** {hint_to_show.strip()}"
            ])

        return "\n".join(lines)


class StepWidgetPayload(BaseModel):
    """
    Complete state payload powering the interactive Stepper Widget on the web UI.
    Contains total steps, active step index, completed history, and all step cards.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    total_steps: int = Field(..., ge=1, description="Total number of steps in the problem")
    current_step_index: int = Field(
        ...,
        ge=0,
        description="0-indexed pointer to the currently active step"
    )
    completed_steps: List[int] = Field(
        default_factory=list,
        description="List of 0-indexed completed step numbers"
    )
    steps: List[SocraticStep] = Field(
        ...,
        description="List of all SocraticStep objects in sequence"
    )
    visual_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional visual scaffolding data for the active exercise"
    )

    def get_active_step(self) -> Optional[SocraticStep]:
        """Returns the currently active step object, or None if index is out of range."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self, recorded_answer: Optional[str] = None) -> bool:
        """
        Marks the current step as completed and advances to the next step.
        Returns True if advanced, False if already at the final step.
        """
        active_step = self.get_active_step()
        if active_step:
            active_step.status = "completed"
            if recorded_answer is not None:
                active_step.student_answer = recorded_answer
            if self.current_step_index not in self.completed_steps:
                self.completed_steps.append(self.current_step_index)

        if self.current_step_index + 1 < self.total_steps:
            self.current_step_index += 1
            next_step = self.get_active_step()
            if next_step and next_step.status != "completed":
                next_step.status = "in_progress"
            return True
        return False

    def jump_to_step(self, target_index: int) -> bool:
        """
        Jumps to a specific step index.
        Returns True if successful, False if target_index is invalid.
        """
        if 0 <= target_index < self.total_steps:
            self.current_step_index = target_index
            target_step = self.steps[target_index]
            if target_step.status == "pending":
                target_step.status = "in_progress"
            return True
        return False

    def to_overview_markdown(self) -> str:
        """
        Renders the clean, question-free roadmap view (Overview Mode).
        Excludes all 'Your Turn' prompts to provide a peaceful bird's-eye solution summary.
        """
        lines = [
            "📋 **Full Solution Journey (Overview Mode)**",
            ""
        ]

        for idx, step in enumerate(self.steps):
            if step.status == "completed":
                status_icon = "✅"
                status_text = f"Solved (Answer: {step.student_answer or step.expected_answer or 'Completed'})"
            elif idx == self.current_step_index:
                status_icon = "🔄"
                status_text = "In Progress (Active Step)"
            else:
                status_icon = "⏳"
                status_text = "Up Next 🔒"

            lines.extend([
                f"{status_icon} **Step {step.step_number}: {step.title}**",
                f"   • Mission: {step.mission}",
                f"   • Rule: {step.clue}",
                f"   • Status: {status_text}",
                ""
            ])

        return "\n".join(lines).strip()


class SocraticResponse(BaseModel):
    """
    Standardized API response contract returned by the orchestrator.
    Emits both structured JSON for the frontend stepper widget and
    formatted Markdown for chat bubble rendering.
    """
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., description="Unique conversation session identifier")
    step_widget: StepWidgetPayload = Field(..., description="Interactive Stepper Widget payload")
    formatted_markdown: str = Field(..., description="Dual-mode rendered markdown response")
    is_problem_complete: bool = Field(default=False, description="True if all steps are successfully solved")
    feedback_message: Optional[str] = Field(
        default=None,
        description="Optional praise or encouraging feedback for the student's previous attempt"
    )
    active_hint: Optional[str] = Field(
        default=None,
        description="Active progressive hint text if student requested help"
    )

    @classmethod
    def from_step_widget(
        cls,
        session_id: str,
        widget: StepWidgetPayload,
        feedback_message: Optional[str] = None,
        active_hint: Optional[str] = None,
        is_problem_complete: bool = False
    ) -> "SocraticResponse":
        """
        Factory helper to build a complete SocraticResponse with synchronized Markdown.
        """
        active_step = widget.get_active_step()
        if active_step:
            card_md = active_step.to_markdown(active_hint=active_hint)
        else:
            card_md = widget.to_overview_markdown()

        if feedback_message:
            formatted_md = f"{feedback_message.strip()}\n\n---\n\n{card_md}"
        else:
            formatted_md = card_md

        return cls(
            session_id=session_id,
            step_widget=widget,
            formatted_markdown=formatted_md,
            is_problem_complete=is_problem_complete,
            feedback_message=feedback_message,
            active_hint=active_hint
        )
