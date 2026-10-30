"""
File: services/science_service/app/prompts/controller.py
Description: Dynamic Prompt Controller for the Unified Science Service.
             Supports physics, chemistry, and biology with scalable grade-level customization (Grades 1-12).
             Defaults to Grade 1–3 for early elementary.
"""

import os
import yaml
from typing import Dict, Any

GRADE_LEVELS = {
    "grade_1_3": {
        "group": "Grade 1-3 (Early Elementary)",
        "guidelines": "Use extremely simple words and everyday examples (plants, water, push/pull, magnets, sun). No complex formulas or abstract jargon. Keep steps visual, gentle, and relatable with emojis."
    },
    "grade_4_6": {
        "group": "Grade 4-6 (Upper Elementary)",
        "guidelines": "Introduce basic scientific concepts (states of matter, photosynthesis, food chains, simple circuits, gravity) in accessible, friendly language with clear cause-and-effect steps."
    },
    "grade_7_9": {
        "group": "Grade 7-9 (Middle School)",
        "guidelines": "Use scientific terms (atoms, cellular organelles, Newton's laws, chemical reactions). Provide structured quantitative and qualitative step-by-step reasoning."
    },
    "grade_10_12": {
        "group": "Grade 10-12 (High School)",
        "guidelines": "Rigorous scientific derivation, standard formulas, stoichiometry, kinematics equations, and biological molecular pathways."
    }
}


class SciencePromptController:
    """
    Builds dynamic prompts for Physics, Chemistry, and Biology solvers.
    """
    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_dir, "templates.yml")
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        return data
            except Exception as e:
                print(f"Warning: Failed to load Science Service templates.yml: {e}")
        return {}

    def get_prompt(self, subject: str, query: str, grade_level: str = "grade_1_3") -> str:
        """
        Builds dynamic prompt tailored to subject and grade level.
        Defaults to Grade 1–3.
        """
        template_key = f"solve_{subject.lower()}_steps"
        grade_info = GRADE_LEVELS.get(grade_level, GRADE_LEVELS["grade_1_3"])
        
        template_data = self.templates.get(template_key)
        if not template_data:
            system = (
                f"You are an expert elementary science tutor solving a problem step-by-step. "
                f"Target audience: {grade_info['group']}. Guidelines: {grade_info['guidelines']}. "
                f"Return ONLY a JSON list of step strings."
            )
            return f"{system}\n\nQuery: {query}"

        system = template_data["system"].format(
            grade_level_group=grade_info["group"],
            grade_level_guidelines=grade_info["guidelines"]
        )
        user = template_data["user"].format(query=query)
        return f"{system}\n\n{user}"


prompt_controller = SciencePromptController()
