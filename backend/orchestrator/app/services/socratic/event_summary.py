"""
File: orchestrator/app/services/socratic/event_summary.py
Description: Structured Event-Based Rolling Session Summary (Sprint 3 - Task 3.2).
             Replaces raw conversational chatter with compact pedagogical code events
             and captures the immediately preceding tutor prompt.
             Guarantees zero expected-answer exposure to downstream LLM interpretation prompts.
"""

import time
import html
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class StepEvent:
    """Represents a discrete pedagogical event during a problem-solving step."""
    step_number: int
    step_type: str                   # e.g., "arithmetic", "fraction", "science_concept"
    objective: str                   # Pedagogical goal WITHOUT the answer
    attempt_count: int = 0
    hints_given: List[str] = field(default_factory=list)  # e.g., ["tier1_clue", "tier2_breakdown"]
    outcome: str = "in_progress"     # "in_progress", "step_completed", "attempt_failed", "hint_requested"
    timestamp: float = field(default_factory=time.time)


@dataclass
class RollingSessionSummary:
    """
    Maintains a bounded window of structured step events and the immediately
    preceding tutor prompt. Designed for minimal token footprint and maximum context safety.
    """
    session_id: str
    subject: str = "math"
    grade_level: int = 2
    active_step_number: int = 1
    max_retained_events: int = 5
    recent_events: List[StepEvent] = field(default_factory=list)
    last_tutor_prompt: str = ""      # Exact text of immediately preceding tutor question

    def set_last_tutor_prompt(self, prompt: str) -> None:
        """Sets the immediately preceding tutor prompt with whitespace trimming."""
        self.last_tutor_prompt = (prompt or "").strip()

    def get_or_create_event(self, step_number: int, step_type: str = "general", objective: str = "") -> StepEvent:
        """Retrieves existing event for step_number or initializes a new one."""
        for ev in self.recent_events:
            if ev.step_number == step_number:
                if objective and not ev.objective:
                    ev.objective = objective
                if step_type != "general" and ev.step_type == "general":
                    ev.step_type = step_type
                return ev

        new_ev = StepEvent(
            step_number=step_number,
            step_type=step_type,
            objective=objective,
        )
        self.recent_events.append(new_ev)
        self._prune()
        return new_ev

    def record_attempt(
        self,
        step_number: int,
        is_correct: bool,
        step_type: str = "general",
        objective: str = "",
    ) -> StepEvent:
        """Records a student answer attempt and updates step outcome."""
        ev = self.get_or_create_event(step_number, step_type, objective)
        ev.attempt_count += 1
        ev.outcome = "step_completed" if is_correct else "attempt_failed"
        ev.timestamp = time.time()
        if is_correct and step_number >= self.active_step_number:
            self.active_step_number = step_number + 1
        return ev

    def record_hint(
        self,
        step_number: int,
        hint_tier: int,
        hint_label: str = "",
        step_type: str = "general",
        objective: str = "",
    ) -> StepEvent:
        """Records a hint given to the student."""
        ev = self.get_or_create_event(step_number, step_type, objective)
        label = hint_label or f"tier{hint_tier}_hint"
        if label not in ev.hints_given:
            ev.hints_given.append(label)
        ev.outcome = "hint_requested"
        ev.timestamp = time.time()
        return ev

    def _prune(self) -> None:
        """Keeps only the most recent N step events to bound prompt tokens."""
        if len(self.recent_events) > self.max_retained_events:
            self.recent_events = self.recent_events[-self.max_retained_events:]

    def to_xml_context(self) -> str:
        """
        Renders the rolling session events into an XML context block.
        Safely escapes user and tutor text to prevent prompt injection.
        """
        lines = [
            f'<session_events active_step="{self.active_step_number}" subject="{html.escape(self.subject)}" grade="{self.grade_level}">'
        ]
        
        for ev in self.recent_events:
            escaped_type = html.escape(ev.step_type)
            escaped_outcome = html.escape(ev.outcome)
            hints_count = len(ev.hints_given)
            lines.append(
                f'  <event step="{ev.step_number}" type="{escaped_type}" outcome="{escaped_outcome}" attempts="{ev.attempt_count}" hints="{hints_count}">'
            )
            if ev.objective:
                lines.append(f'    <objective>{html.escape(ev.objective)}</objective>')
            for h in ev.hints_given:
                lines.append(f'    <hint tier="{html.escape(h)}" />')
            lines.append('  </event>')

        if self.last_tutor_prompt:
            escaped_prompt = html.escape(self.last_tutor_prompt)
            lines.append(f'  <last_tutor_prompt>{escaped_prompt}</last_tutor_prompt>')

        lines.append('</session_events>')
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes session summary to a dictionary for LangGraph state."""
        return {
            "session_id": self.session_id,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "active_step_number": self.active_step_number,
            "max_retained_events": self.max_retained_events,
            "recent_events": [asdict(e) for e in self.recent_events],
            "last_tutor_prompt": self.last_tutor_prompt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollingSessionSummary":
        """Deserializes session summary from LangGraph state dictionary."""
        events_data = data.get("recent_events", [])
        events = [
            StepEvent(
                step_number=e["step_number"],
                step_type=e.get("step_type", "general"),
                objective=e.get("objective", ""),
                attempt_count=e.get("attempt_count", 0),
                hints_given=e.get("hints_given", []),
                outcome=e.get("outcome", "in_progress"),
                timestamp=e.get("timestamp", 0.0),
            )
            for e in events_data
        ]
        return cls(
            session_id=data.get("session_id", "default_session"),
            subject=data.get("subject", "math"),
            grade_level=data.get("grade_level", 2),
            active_step_number=data.get("active_step_number", 1),
            max_retained_events=data.get("max_retained_events", 5),
            recent_events=events,
            last_tutor_prompt=data.get("last_tutor_prompt", ""),
        )
