"""
File: orchestrator/app/services/nodes/nlu_pipeline.py
Description: Implementation of the 5-Layered Query Understanding NLU Pipeline
             in the Socratic Tutor Orchestrator, using deterministic cleaning and Gemini classification.
"""

import re
import os
from typing import List, Dict, Any, Tuple
import google.generativeai as genai
from app.services.prompts import prompt_controller
from app.core.logging import logger

# Initialize Gemini safely
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class NLUPipeline:
    """
    Executes the 5-layered Query Understanding NLU pipeline.
    """
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash") if GEMINI_API_KEY else None

    def layer_1_normalize(self, query: str) -> str:
        """
        Layer 1: Deterministic Pre-processing & Normalization.
        Standardizes mathematical and physical units / expressions.
        """
        # Replace multiplication representations
        cleaned = re.sub(r'(\d)\s*[xX×•]\s*([a-zA-Z\d\()][a-zA-Z\d\(\)]*)', r'\1*\2', query)
        cleaned = re.sub(r'([a-zA-Z])\s*[xX×•]\s*(\d)', r'\1*\2', cleaned)
        
        # Standardize exponent caret to double asterisk
        cleaned = cleaned.replace('^', '**')
        
        # Replace standard arrow indicators for equations
        cleaned = cleaned.replace('-->', '->').replace('==>', '->').replace('=', '->') if '->' not in cleaned and '=' in cleaned else cleaned
        
        return cleaned.strip()

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """
        Helper to format conversation history list into a text block for prompt injection.
        """
        if not history:
            return "No previous conversation history."
        formatted = []
        for turn in history[-5:]:  # Analyze last 5 turns to preserve tokens
            role = "Student" if turn.get("role") == "user" else "Tutor"
            content = turn.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    def layer_2_classify_intent(self, query: str, formatted_history: str, history_len: int) -> str:
        """
        Layer 2: Intent Classification (LLM).
        """
        # Fast pathway for empty history (usually starting a new solve)
        if history_len == 0:
            # Check for simple greetings
            if query.lower() in ["hi", "hello", "hey", "hola", "greetings", "thanks", "thank you"]:
                return "CHITCHAT"
            return "INITIAL_SOLVE"

        if not self.model:
            return "INITIAL_SOLVE"

        try:
            prompt = prompt_controller.get_intent_prompt(query, formatted_history)
            response = self.model.generate_content(prompt)
            intent = response.text.strip().upper()
            
            # Map back to valid categories
            valid_intents = {"INITIAL_SOLVE", "STEP_ATTEMPT", "CLARIFY", "REQUEST_PRACTICE", "CHITCHAT"}
            for valid in valid_intents:
                if valid in intent:
                    return valid
            return "INITIAL_SOLVE"
        except Exception as e:
            logger.error(f"NLU Layer 2 (Intent) failed: {e}")
            return "INITIAL_SOLVE"

    def layer_3_route_subject(self, query: str) -> str:
        """
        Layer 3: Subject Routing (LLM).
        """
        if not self.model:
            return "GENERAL"

        try:
            prompt = prompt_controller.get_classification_prompt(query)
            response = self.model.generate_content(prompt)
            subject = response.text.strip().upper()
            
            valid_subjects = {"MATH", "PHYSICS", "CHEMISTRY", "BIOLOGY", "GENERAL"}
            for valid in valid_subjects:
                if valid in subject:
                    return valid
            return "GENERAL"
        except Exception as e:
            logger.error(f"NLU Layer 3 (Subject) failed: {e}")
            return "GENERAL"

    def layer_4_resolve_coreference(self, query: str, formatted_history: str, history_len: int) -> str:
        """
        Layer 4: Conversational Coreference Resolution (LLM).
        Resolves pronouns like 'it', 'this' to their reference terms.
        """
        if history_len == 0 or not self.model:
            return query

        try:
            prompt = prompt_controller.get_coreference_prompt(query, formatted_history)
            response = self.model.generate_content(prompt)
            resolved = response.text.strip()
            return resolved if resolved else query
        except Exception as e:
            logger.error(f"NLU Layer 4 (Coreference) failed: {e}")
            return query

    def layer_0_translate_input(self, query: str) -> str:
        """
        Layer 0: Input Translation (Khmer -> English).
        Translates raw input query if language context is set to Khmer.
        """
        if not self.model:
            return query
        try:
            prompt = prompt_controller.get_translation_to_english_prompt(query)
            response = self.model.generate_content(prompt)
            translated = response.text.strip()
            return translated if translated else query
        except Exception as e:
            logger.error(f"NLU Layer 0 (Input Translation) failed: {e}")
            return query

    def layer_5_extract_keywords(self, query: str) -> str:
        """
        Layer 5: RAG Concept & Search Term Extractor (LLM).
        """
        if not self.model:
            return query

        try:
            prompt = prompt_controller.get_concept_prompt(query)
            response = self.model.generate_content(prompt)
            keywords = response.text.strip()
            return keywords if keywords else query
        except Exception as e:
            logger.error(f"NLU Layer 5 (Keywords) failed: {e}")
            return query


    def execute_pipeline(self, raw_query: str, history: List[Dict[str, str]], language: str = "en") -> Dict[str, Any]:
        """
        Runs all NLU pipeline layers (including Layer 0 translation) and returns structured results.
        """
        logger.info(f"NLU Pipeline: processing user input (language={language})...")
        
        # Layer 0: Translate input query to English if language context is Khmer
        original_query = raw_query
        if language == "khmer":
            logger.info("NLU Layer 0: Translating Khmer input to English...")
            english_query = self.layer_0_translate_input(raw_query)
            logger.info(f"NLU Layer 0: Translated query: {english_query}")
        else:
            english_query = raw_query

        # Layer 1: Normalize
        normalized_query = self.layer_1_normalize(english_query)
        
        # Format history block
        formatted_history = self._format_history(history)
        history_len = len(history)
        
        # Layer 2: Intent
        intent = self.layer_2_classify_intent(normalized_query, formatted_history, history_len)
        logger.info(f"NLU Layer 2 Intent: {intent}")
        
        # Layer 3: Subject Routing
        # Default to previous subject if they are doing step attempts, practice or clarifying
        subject = "GENERAL"
        if intent in ["INITIAL_SOLVE", "CLARIFY"]:
            subject = self.layer_3_route_subject(normalized_query)
        logger.info(f"NLU Layer 3 Subject: {subject}")
        
        # Layer 4: Coreference Resolution
        resolved_query = self.layer_4_resolve_coreference(normalized_query, formatted_history, history_len)
        logger.info(f"NLU Layer 4 Resolved: {resolved_query}")
        
        # Layer 5: RAG Keyword Extraction
        keywords = self.layer_5_extract_keywords(resolved_query)
        logger.info(f"NLU Layer 5 Keywords: {keywords}")
        
        return {
            "query": normalized_query,
            "original_raw_query": original_query,
            "user_intent": intent,
            "subject": subject,
            "resolved_query": resolved_query,
            "search_keywords": keywords
        }

nlu_pipeline = NLUPipeline()

