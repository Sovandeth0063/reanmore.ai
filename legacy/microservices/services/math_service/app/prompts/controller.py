"""
File: services/math_service/app/prompts/controller.py
Description: Dynamic Prompt Controller class for Math Service. Loads templates 
             from templates.yml and formats them with grade-level parameters (Grades 1-12).
             Defaults to Grade 1–3 for early elementary.
"""

import os
import yaml
from typing import Dict, Any

GRADE_LEVELS = {
    "grade_1_3": {
        "group": "Grade 1-3 (Early Elementary / Primary School)",
        "guidelines": "Use extremely simple words, single and double digit numbers. Avoid algebraic variables (like x, y) or formulas. Explain using basic arithmetic operations (+, -, *, /) and real-world counting items (e.g. apples, cookies, stickers) instead of abstract variables."
    },
    "grade_4_6": {
        "group": "Grade 4-6 (Upper Elementary)",
        "guidelines": "Use simple variables (like x) and basic linear operations. Explain calculations clearly with fractions, basic equations, and arithmetic breakdowns."
    },
    "grade_7_9": {
        "group": "Grade 7-9 (Middle School)",
        "guidelines": "Multi-step algebraic equations, geometry formulas, percentages, ratios, and clear mathematical reasoning."
    },
    "grade_10_12": {
        "group": "Grade 10-12 (High School)",
        "guidelines": "Advanced algebra, trigonometry, quadratics, calculus, and formal mathematical notation."
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

    def get_solver_prompt(self, query: str, grade_level: str = "grade_1_3") -> str:
        """
        Builds the dynamic prompt tailored to the student's grade level.
        Defaults to Grade 1–3.
        """
        grade_info = GRADE_LEVELS.get(grade_level, GRADE_LEVELS["grade_1_3"])
        system = self.templates["solve_math_steps"]["system"].format(
            grade_level_group=grade_info["group"],
            grade_level_guidelines=grade_info["guidelines"]
        )
        user = self.templates["solve_math_steps"]["user"].format(query=query)
        return f"{system}\n\n{user}"


prompt_controller = PromptController()
