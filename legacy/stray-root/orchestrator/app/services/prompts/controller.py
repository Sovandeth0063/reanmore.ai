"""
File: orchestrator/app/services/prompts/controller.py
Description: Dynamic Prompt Controller class implementation for compiling and managing prompts.
             Loads templates dynamically from templates.yml with local Python fallback dictionary.
             Supports grade-level adaptive instructions and NLU pipeline formatting.
"""

import os
import yaml
from typing import Dict, Any

# Grade level guidelines map
GRADE_LEVELS = {
    "grade_1_3": {
        "group": "Grade 1-3 (Elementary / Primary School)",
        "guidelines": (
            "Use extremely simple words and numbers. Avoid algebraic variables (like x, y) or formulas. "
            "Explain using basic arithmetic operations and real-world counting items (e.g. apples, cookies) instead of variables."
        )
    },
    "grade_4_6": {
        "group": "Grade 4-6 (Upper Primary)",
        "guidelines": (
            "Use simple explanations. Introduce basic variables (e.g., x) gently. "
            "Focus on basic equations, fractions, and simple arithmetic steps. Avoid advanced science jargon."
        )
    },
    "grade_7_9": {
        "group": "Grade 7-9 (Secondary School)",
        "guidelines": (
            "Introduce algebraic equations, basic variable manipulation, and introductory physics/chemistry concepts. "
            "Explain relationships step-by-step with intermediate vocabulary."
        )
    },
    "grade_10_12": {
        "group": "Grade 10-12 (High School)",
        "guidelines": (
            "Use formal algebraic notation, rigorous calculations, complex equations, and advanced scientific math functions if needed. "
            "Use precise and academic vocabulary."
        )
    }
}

# Local fallback templates in case templates.yml fails to load or is missing
DEFAULT_TEMPLATES = {
    "classification": {
        "system": (
            "Classify the following query into one of these categories: "
            "MATH, PHYSICS, CHEMISTRY, BIOLOGY, or GENERAL. "
            "Return ONLY the category name as a single word in uppercase. "
            "Do not include formatting, quotes, or markdown."
        ),
        "user": "Query: {query}"
    },
    "intent_classification": {
        "system": (
            "Analyze the user's latest query in the context of the conversation and classify their intent into exactly ONE of the following options:\n"
            "- 'INITIAL_SOLVE': Starting a new science question.\n"
            "- 'STEP_ATTEMPT': Submitting an attempt for an ongoing exercise.\n"
            "- 'CLARIFY': Asking a conceptual question or 'why/how'.\n"
            "- 'REQUEST_PRACTICE': Asking for another practice example.\n"
            "- 'CHITCHAT': Greetings or casual chatter.\n\n"
            "Return ONLY the intent label as a single word in uppercase."
        ),
        "user": "Chat History:\n{chat_history}\n\nLatest Query: '{query}'"
    },
    "coreference_resolution": {
        "system": (
            "Examine the conversation history and rewrite the user's latest query to resolve pronouns (it, this, that) with their original nouns.\n"
            "Return ONLY the rewritten query text."
        ),
        "user": "Chat History:\n{chat_history}\n\nLatest Query: '{query}'"
    },
    "concept_extraction": {
        "system": (
            "Extract the core scientific concepts, keywords, and equations from the query. Filter filler words.\n"
            "Return ONLY the space-separated list of keywords."
        ),
        "user": "Query: '{query}'"
    },
    "translate_khmer_to_english": {
        "system": (
            "Translate the following Khmer text to English. Keep math formulas/equations exactly as-is. "
            "Return ONLY the English text."
        ),
        "user": "Text to translate: '{text}'"
    },
    "translate_english_to_khmer": {
        "system": (
            "Translate the following English text to Khmer. Keep math equations, variables, and LaTeX symbols exactly as-is. "
            "Return ONLY the Khmer text."
        ),
        "user": "Text to translate: '{text}'"
    },
    "rolling_summary": {
        "system": (
            "You are a summarization assistant. Update the following running summary of a tutoring conversation "
            "with these newly evicted turns. Keep the summary concise and focused on the student's progress and active task."
        ),
        "user": "Current Summary: '{rolling_summary}'\n\nNew Turns:\n{evicted_turns}\n\nNew updated summary (keep it under 400 characters):"
    },


    "socratic_tutor": {
        "system": (
            "You are a friendly Socratic science tutor specializing in {subject}.\n"
            "Your absolute core objective is to guide students step-by-step. NEVER reveal the final answer or next formula solution directly.\n"
            "Tutor Persona: {persona_style}\n\n"
            "Target Student Group: {grade_level_group}\n"
            "Tutor Language & Detail Level Guidelines: {grade_level_guidelines}\n\n"
            "--- CURRENT STEP CONTEXT ---\n"
            "Step Index: {step_num} of {total_steps}\n"
            "Expected Math/Science formulation: '{expected_expression}'\n"
            "Hint Count (consecutive errors): {hint_count}\n"
            "Hint Level Guidance: {hint_guidance}\n"
            "----------------------------\n\n"
            "Instructions:\n"
            "1. Be extremely supportive. Praise correct logic, but nudge them gently for mistakes.\n"
            "2. Keep your responses short (2-3 sentences max) to maintain high engagement.\n"
            "3. Use LaTeX formatting for mathematical expressions (e.g., $2x + 4 = 10$).\n"
            "4. Do not include markdown code blocks or tell the student about the 'expected steps' context variables."
        ),
        "user": "Student's latest step attempt: '{student_attempt}'"
    },
    "practice_generator": {
        "system": (
            "You are an educational curriculum creator.\n"
            "The student has successfully solved the following query: '{original_query}'.\n"
            "Generate a SIMILAR practice exercise for the subject '{subject}' with a similar difficulty level.\n"
            "Return ONLY the new exercise text as a single plain-text question. Do not include answers, explanations, greetings, or markdown formatting. Just the raw question."
        )
    }
}

class PromptController:
    """
    Manages and formats prompt templates for the Socratic Tutor Orchestrator.
    """
    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        """
        Dynamically loads templates from local templates.yml file.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_dir, "templates.yml")
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    templates = yaml.safe_load(f)
                    if templates:
                        # Merge loaded templates with fallback to ensure all keys exist
                        merged = DEFAULT_TEMPLATES.copy()
                        merged.update(templates)
                        return merged
            except Exception as e:
                print(f"Warning: Failed to load templates.yml: {e}. Using DEFAULT_TEMPLATES fallbacks.")
        return DEFAULT_TEMPLATES

    def get_classification_prompt(self, query: str) -> str:
        """
        Formats the classification prompt for Gemini.
        """
        system = self.templates["classification"]["system"]
        user = self.templates["classification"]["user"].format(query=query)
        return f"{system}\n\n{user}"

    def get_intent_prompt(self, query: str, chat_history: str) -> str:
        """
        Formats the intent classification prompt.
        """
        system = self.templates["intent_classification"]["system"]
        user = self.templates["intent_classification"]["user"].format(query=query, chat_history=chat_history)
        return f"{system}\n\n{user}"

    def get_coreference_prompt(self, query: str, chat_history: str) -> str:
        """
        Formats the contextual coreference resolution prompt.
        """
        system = self.templates["coreference_resolution"]["system"]
        user = self.templates["coreference_resolution"]["user"].format(query=query, chat_history=chat_history)
        return f"{system}\n\n{user}"

    def get_concept_prompt(self, query: str) -> str:
        """
        Formats the concept/keyword extraction prompt for RAG search.
        """
        system = self.templates["concept_extraction"]["system"]
        user = self.templates["concept_extraction"]["user"].format(query=query)
        return f"{system}\n\n{user}"

    def get_translation_to_english_prompt(self, text: str) -> str:
        """
        Formats the Khmer to English translation prompt.
        """
        system = self.templates["translate_khmer_to_english"]["system"]
        user = self.templates["translate_khmer_to_english"]["user"].format(text=text)
        return f"{system}\n\n{user}"

    def get_translation_to_khmer_prompt(self, text: str) -> str:
        """
        Formats the English to Khmer translation prompt.
        """
        system = self.templates["translate_english_to_khmer"]["system"]
        user = self.templates["translate_english_to_khmer"]["user"].format(text=text)
        return f"{system}\n\n{user}"


    def get_tutor_prompt(
        self,
        subject: str,
        solved_steps: list,
        current_step_index: int,
        hint_count: int,
        student_attempt: str,
        grade_level: str = "grade_10_12",
        persona_style: str = "Supportive & Engaging Socratic Coach"
    ) -> str:
        """
        Builds the system prompt for the tutor, adapting the hinting level based on mistake count
        and targeting the student's grade level.
        """
        expected_step = solved_steps[current_step_index] if current_step_index < len(solved_steps) else {}
        expected_expression = expected_step.get("expression", "N/A")
        predefined_hint = expected_step.get("hint", "N/A")
        
        # Get grade details
        grade_info = GRADE_LEVELS.get(grade_level, GRADE_LEVELS["grade_10_12"])
        grade_group = grade_info["group"]
        grade_guidelines = grade_info["guidelines"]

        # Calculate hint guidance level dynamically based on hint_count
        if hint_count == 0:
            hint_guidance = (
                f"This is the student's first attempt. If their answer is wrong, "
                f"give them a very high-level conceptual hint or ask a leading question. "
                f"Predefined hint reference: '{predefined_hint}'"
            )
        elif hint_count == 1:
            hint_guidance = (
                f"This is the student's second attempt. If their answer is wrong, "
                f"provide a more direct hint highlighting the operation they need to execute. "
                f"Predefined hint reference: '{predefined_hint}'"
            )
        else:
            hint_guidance = (
                f"The student has failed multiple times (3+ attempts). If their answer is wrong, "
                f"break down the step into a simplified sub-step or an easy calculation. "
                f"Simplify the scope of the question so they can gain confidence, but do not state the final step answer directly."
            )
            
        system = self.templates["socratic_tutor"]["system"].format(
            subject=subject,
            persona_style=persona_style,
            grade_level_group=grade_group,
            grade_level_guidelines=grade_guidelines,
            step_num=current_step_index + 1,
            total_steps=len(solved_steps),
            expected_expression=expected_expression,
            hint_count=hint_count,
            hint_guidance=hint_guidance
        )
        user = self.templates["socratic_tutor"]["user"].format(student_attempt=student_attempt)
        
        return f"{system}\n\n{user}"

    def get_practice_prompt(self, original_query: str, subject: str) -> str:
        """
        Formats the prompt to generate an analogous practice question.
        """
        return self.templates["practice_generator"]["system"].format(
            original_query=original_query,
            subject=subject
        )

    def get_rolling_summary_prompt(self, rolling_summary: str, evicted_turns: str) -> str:
        """
        Formats the rolling summary prompt for conversation history compaction.
        """
        system = self.templates["rolling_summary"]["system"]
        user = self.templates["rolling_summary"]["user"].format(
            rolling_summary=rolling_summary,
            evicted_turns=evicted_turns
        )
        return f"{system}\n\n{user}"


# Instantiate global prompt controller
prompt_controller = PromptController()
