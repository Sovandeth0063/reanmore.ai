"""
File: orchestrator/app/services/socratic/skills/__init__.py
Description: Package initializer for the Core Elementary Math Skill Templates:
             - add_within_10 (simplest sums, registered before make-a-ten)
             - sub_within_10 (simplest differences, registered before hop-back)
             - add_within_20
             - sub_within_20
             - add_2digit_regroup
             - sub_2digit_borrow
             - mult_tables
             - fraction_equivalent
             - one_step_word_problem
"""

from app.services.socratic.skills.base import Skill, StepTemplate, SkillRegistry, skill_registry

# Import all skills to trigger registration in singleton skill_registry.
# Order matters: the first matching skill wins. Word problems are routed first,
# then very simple sums, then the more abstract strategies.
from app.services.socratic.skills import (
    one_step_word_problem,
    add_within_10,
    sub_within_10,
    add_within_20,
    sub_within_20,
    add_2digit_regroup,
    sub_2digit_borrow,
    mult_tables,
    fraction_equivalent,
)

__all__ = [
    "Skill",
    "StepTemplate",
    "SkillRegistry",
    "skill_registry",
]
