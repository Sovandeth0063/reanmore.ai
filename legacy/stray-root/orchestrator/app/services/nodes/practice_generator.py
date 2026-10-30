"""
File: orchestrator/app/services/nodes/practice_generator.py
Description: LangGraph node that generates analogous science practice problems using 
             the dynamic PromptController and resets the tutor step loop.
"""

import google.generativeai as genai
from app.core.config import settings
from app.core.logging import logger
from app.services.state import SocraticTutorState
from app.services.prompts import prompt_controller

async def generate_practice_node(state: SocraticTutorState) -> dict:
    """
    LangGraph node to generate a similar practice question based on the original query.
    """
    subject = state.get("subject", "GENERAL")
    original_query = state.get("original_query") or state.get("query", "")
    
    logger.info(f"Practice Generator Node: Creating similar example for: '{original_query}'")
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = prompt_controller.get_practice_prompt(original_query, subject)
        response = model.generate_content(prompt)
        new_query = response.text.strip()
    except Exception as e:
        logger.error(f"Gemini practice generation failed: {e}")
        if subject == "MATH":
            new_query = "solve 3*x + 6 = 15"
        else:
            new_query = "Explain photosynthesis"
            
    logger.info(f"Practice Generator Node: Generated new exercise: '{new_query}'")
    
    return {
        "original_query": original_query,
        "query": new_query,
        "practice_mode": True,
        "solved_steps": [], # Cleared to trigger solver service lookup in tutor_loop_node
        "current_step_index": 0,
        "hint_count": 0,
        "student_attempt": "",
        "tutor_feedback": f"I have generated a similar practice problem: '{new_query}'. Let's solve it together! What is the first step?"
    }
