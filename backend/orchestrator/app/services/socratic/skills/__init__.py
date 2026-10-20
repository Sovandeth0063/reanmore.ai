"""
File: orchestrator/app/services/socratic/skills/__init__.py
Description: Package initializer for the 6 Core Elementary Math Skill Templates:
             - add_within_20
             - sub_within_20
             - add_2digit_regroup
             - sub_2digit_borrow
             - mult_tables
             - fraction_equivalent
             - one_step_word_problem
"""

from app.services.socratic.skills.base import Skill, StepTemplate, SkillRegistry, skill_registry

# Import all skills to trigger registration in singleton skill_registry
# Word problem skill is registered first so word problems are routed appropriately
from app.services.socratic.skills import (
    one_step_word_problem,
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
