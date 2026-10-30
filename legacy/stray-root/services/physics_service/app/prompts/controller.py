"""
File: services/physics_service/app/prompts/controller.py
Description: Dynamic Prompt Controller class for Physics Service. Loads templates 
             from templates.yml and formats them with grade-level parameters.
"""

import os
import yaml
from typing import Dict, Any

GRADE_LEVELS = {
    "grade_1_3": {
        "group": "Grade 1-3 (Elementary / Primary School)",
        "guidelines": "Use extremely simple words and numbers. Avoid physics symbols (like v, u, a, t) or complex formulas. Describe motion using visual items (e.g. rolling ball, falling apple) and keep calculations to basic addition or subtraction."
    },
    "grade_4_6": {
        "group": "Grade 4-6 (Upper Primary)",
        "guidelines": "Use simple explanations. Introduce basic terms (like speed, force, mass) gently. Focus on basic calculations like speed = distance / time. Avoid algebraic formula derivations."
    },
    "grade_7_9": {
        "group": "Grade 7-9 (Secondary School)",
        "guidelines": "Introduce kinematics equations (v = u + a*t) and force equations (F = m*a). Use variable notation and standard scientific terms (gravity, force, mass, acceleration)."
    },
    "grade_10_12": {
        "group": "Grade 10-12 (High School)",
        "guidelines": "Use rigorous scientific vocabulary, complete kinematics/forces formula derivations, standard units (m/s, m/s^2, N), and precise calculations."
    }
}

DEFAULT_TEMPLATES = {
    "solve_physics_steps": {
        "system": (
            "You are an expert physics step-by-step solver. "
            "Solve the user's physics query and compile the sequence of solution steps. "
            "The explanations, formulas, and vocabulary MUST be tailored exactly for: {grade_level_group}. "
            "Grade Group Guidelines: {grade_level_guidelines} "
            "Return ONLY a valid JSON list of step strings. Do not include markdown tags or extra text."
        ),
        "user": "Query: {query}"
    }
}

class PromptController:
    """
    Loads templates and builds prompts for AI physics solving.
    """
    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_dir, "templates.yml")
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    templates = yaml.safe_load(f)
                    if templates and "solve_physics_steps" in templates:
                        return templates
            except Exception as e:
                print(f"Warning: Failed to load Physics Service templates.yml: {e}")
        return DEFAULT_TEMPLATES

    def get_solver_prompt(self, query: str, grade_level: str = "grade_10_12") -> str:
        """
        Builds the dynamic prompt tailored to the student's grade level.
        """
        grade_info = GRADE_LEVELS.get(grade_level, GRADE_LEVELS["grade_10_12"])
        system = self.templates["solve_physics_steps"]["system"].format(
            grade_level_group=grade_info["group"],
            grade_level_guidelines=grade_info["guidelines"]
        )
        user = self.templates["solve_physics_steps"]["user"].format(query=query)
        return f"{system}\n\n{user}"

prompt_controller = PromptController()
