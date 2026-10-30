"""
File: services/biology_service/app/prompts/controller.py
Description: Dynamic Prompt Controller class for Biology Service. Loads templates 
             from templates.yml and formats them with grade-level parameters.
"""

import os
import yaml
from typing import Dict, Any

GRADE_LEVELS = {
    "grade_1_3": {
        "group": "Grade 1-3 (Elementary / Primary School)",
        "guidelines": "Use extremely simple words and descriptions. Avoid complex scientific terms (like mitochondria, ribosomes, meiosis) or structural symbols. Discuss concepts using daily visual concepts (e.g. plants growing, animals breathing, energy) and keep explanations extremely basic."
    },
    "grade_4_6": {
        "group": "Grade 4-6 (Upper Primary)",
        "guidelines": "Use simple explanations. Introduce basic terms (like cells, organs, habitats) gently. Describe processes conceptually with visual breakdowns and avoid detailed molecular names."
    },
    "grade_7_9": {
        "group": "Grade 7-9 (Secondary School)",
        "guidelines": "Introduce cellular structure (nucleus, membrane), genetics concepts, and basic process steps (mitosis, photosynthesis). Use standard biological terms and explain relationships clearly."
    },
    "grade_10_12": {
        "group": "Grade 10-12 (High School)",
        "guidelines": "Use rigorous scientific vocabulary, detailed biochemical processes (transcription, translation, codon mappings), genetic terms (alleles, genotypes), and precise explanations."
    }
}

DEFAULT_TEMPLATES = {
    "solve_biology_steps": {
        "system": (
            "You are an expert biology step-by-step solver. "
            "Solve the user's biology query and compile the sequence of solution steps. "
            "The explanations, terms, and vocabulary MUST be tailored exactly for: {grade_level_group}. "
            "Grade Group Guidelines: {grade_level_guidelines} "
            "Return ONLY a valid JSON list of step strings. Do not include markdown tags or extra text."
        ),
        "user": "Query: {query}"
    }
}

class PromptController:
    """
    Loads templates and builds prompts for AI biology solving.
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
                    if templates and "solve_biology_steps" in templates:
                        return templates
            except Exception as e:
                print(f"Warning: Failed to load Biology Service templates.yml: {e}")
        return DEFAULT_TEMPLATES

    def get_solver_prompt(self, query: str, grade_level: str = "grade_10_12") -> str:
        """
        Builds the dynamic prompt tailored to the student's grade level.
        """
        grade_info = GRADE_LEVELS.get(grade_level, GRADE_LEVELS["grade_10_12"])
        system = self.templates["solve_biology_steps"]["system"].format(
            grade_level_group=grade_info["group"],
            grade_level_guidelines=grade_info["guidelines"]
        )
        user = self.templates["solve_biology_steps"]["user"].format(query=query)
        return f"{system}\n\n{user}"

prompt_controller = PromptController()
