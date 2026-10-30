"""
File: services/math_service/app/prompts/controller.py
Description: Dynamic Prompt Controller class for Math Service. Loads templates 
             from templates.yml and formats them with grade-level parameters.
"""

import os
import yaml
from typing import Dict, Any

GRADE_LEVELS = {
    "grade_1_3": {
        "group": "Grade 1-3 (Elementary / Primary School)",
        "guidelines": "Use extremely simple words and numbers. Avoid algebraic variables (like x, y) or formulas. Explain using basic arithmetic operations and real-world counting items (e.g. apples, cookies) instead of variables."
    },
    "grade_4_6": {
        "group": "Grade 4-6 (Upper Primary)",
        "guidelines": "Use simple variables (like x) and basic linear operations. Explain calculations clearly with fractions, basic equations, and arithmetic breakdowns."
    },
    "grade_7_9": {
        "group": "Grade 7-9 (Middle School)",
        "guidelines": "Use variables, basic algebraic equations, and standard terminology. Break down steps like isolating variables, simplifying terms."
    },
    "grade_10_12": {
        "group": "Grade 10-12 (High School)",
        "guidelines": "Use formal algebraic notation, rigorous calculations, complex equations, and advanced scientific math functions if needed."
    }
}

DEFAULT_TEMPLATES = {
    "solve_math_steps": {
        "system": (
            "You are an expert mathematical step-by-step solver. "
            "Solve the user's math query and compile the sequence of solution steps. "
            "The explanations, mathematical concepts, and vocabulary MUST be tailored exactly for: {grade_level_group}. "
            "Grade Group Guidelines: {grade_level_guidelines} "
            "Return ONLY a valid JSON list of step strings. Do not include markdown tags or extra text."
        ),
        "user": "Query: {query}"
    }
}

class PromptController:
    """
    Loads templates and builds prompts for AI math solving.
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
                    if templates and "solve_math_steps" in templates:
                        return templates
            except Exception as e:
                print(f"Warning: Failed to load Math Service templates.yml: {e}")
        return DEFAULT_TEMPLATES

    def get_solver_prompt(self, query: str, grade_level: str = "grade_10_12") -> str:
        """
        Builds the dynamic prompt tailored to the student's grade level.
        """
        grade_info = GRADE_LEVELS.get(grade_level, GRADE_LEVELS["grade_10_12"])
        system = self.templates["solve_math_steps"]["system"].format(
            grade_level_group=grade_info["group"],
            grade_level_guidelines=grade_info["guidelines"]
        )
        user = self.templates["solve_math_steps"]["user"].format(query=query)
        return f"{system}\n\n{user}"

prompt_controller = PromptController()
