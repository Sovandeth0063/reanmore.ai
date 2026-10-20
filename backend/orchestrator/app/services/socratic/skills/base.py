"""
File: orchestrator/app/services/socratic/skills/base.py
Description: Abstract protocol, data models, and registry for the Socratic Skill Template Library.
             Adheres to Architecture v2.1 Section 7.1 and 7.2.
"""

from typing import Protocol, List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StepTemplate(BaseModel):
    """
    Template for a single Socratic milestone step card adhering to the 4-part specification:
    1. Mission (🌟)
    2. Clue (💡)
    3. Helpful Example (🍎 - with distinct parallel numbers)
    4. Your Turn (👉 - single question on student's problem)
    """
    step_number: int
    title: str
    mission: str
    clue: str
    helpful_example: str
    your_turn: str
    expected_answer: str
    concept: str
    visual_spec: Optional[Dict[str, Any]] = None
    hints: List[str] = Field(default_factory=list)


class Skill(Protocol):
    """Protocol that every elementary math skill template must implement."""
    skill_id: str
    grade_band: str  # "grade_1_3" | "grade_4_6"

    def matches(self, problem: Dict[str, Any]) -> bool:
        """Determines whether the given problem dictionary belongs to this skill."""
        ...

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        """Generates 2 to 4 verified pedagogical milestone steps."""
        ...

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produces a parallel isomorphic worked example with numbers that have ZERO
        intersection with the student's problem operands or target answers.
        """
        ...


class SkillRegistry:
    """Registry coordinating all elementary math skill templates."""
    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.skill_id] = skill

    def get(self, skill_id: str) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def match(self, problem: Dict[str, Any]) -> Optional[Skill]:
        for skill in self._skills.values():
            if skill.matches(problem):
                return skill
        return None

    def list_skills(self) -> List[str]:
        return list(self._skills.keys())


# Singleton skill registry instance
skill_registry = SkillRegistry()
