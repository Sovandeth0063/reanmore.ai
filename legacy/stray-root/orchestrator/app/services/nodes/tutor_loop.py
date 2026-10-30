"""
File: orchestrator/app/services/nodes/tutor_loop.py
Description: LangGraph tutor loop node that calls solver microservices to compile solution
             paths, validates student steps, and manages step progression state.
"""

from app.core.config import settings
from app.core.logging import logger
from app.services.state import SocraticTutorState
from app.infrastructure.clients import solver_client

async def tutor_loop_node(state: SocraticTutorState) -> dict:
    """
    Main LangGraph node that:
    1. Initializes steps using solver services if solved_steps is empty.
    2. Validates student step attempts against expected solution steps.
    """
    try:
        subject = state.get("subject", "GENERAL")
        solved_steps = state.get("solved_steps", [])
        current_index = state.get("current_step_index", 0)
        student_attempt = state.get("student_attempt", "").strip()
        query = state.get("query", "").strip()

        # 1. INITIAL STATE: solved_steps is empty. Query downstream service to get expected steps.
        if not solved_steps:
            logger.info(f"Tutor Loop Node: Initializing solution path steps for {subject} query...")
            
            if subject == "MATH":
                url = settings.MATH_SERVICE_URL
            elif subject == "PHYSICS":
                url = settings.PHYSICS_SERVICE_URL
            elif subject == "CHEMISTRY":
                url = settings.CHEMISTRY_SERVICE_URL
            elif subject == "BIOLOGY":
                url = settings.BIOLOGY_SERVICE_URL
            else:
                # GENERAL
                return {
                    "solved_steps": [{"step_num": 1, "expression": "GENERAL", "hint": "General reasoning query."}],
                    "current_step_index": 0,
                    "tutor_feedback": "" # Let hint_generator node directly reply
                }

            grade_level = state.get("grade_level", "grade_10_12")
            result = await solver_client.solve(subject, url, query, grade_level)
            if result.get("success") and result.get("steps"):
                steps_list = []
                raw_steps = result.get("steps", [])
                for idx, step_str in enumerate(raw_steps):
                    steps_list.append({
                        "step_num": idx + 1,
                        "expression": step_str,
                        "hint": f"Look at step: {step_str}"
                    })
                
                first_hint = f"Let's solve this exercise together: '{query}'. What is the first step we should take?"
                return {
                    "solved_steps": steps_list,
                    "current_step_index": 0,
                    "tutor_feedback": first_hint,
                    "hint_count": 0
                }
            else:
                logger.warning(f"Downstream solver failed to compile steps. Falling back to GENERAL LLM solver.")
                return {
                    "subject": "GENERAL",
                    "solved_steps": [{"step_num": 1, "expression": "GENERAL", "hint": "General reasoning query."}],
                    "current_step_index": 0,
                    "tutor_feedback": ""
                }

        # 2. EVALUATION STATE: check student's attempt against current expected step
        if current_index >= len(solved_steps):
            return {"tutor_feedback": "You've already solved this exercise! Let me know if you want another practice question."}

        expected_step_dict = solved_steps[current_index]
        expected_expression = expected_step_dict.get("expression", "")

        # Perform validation based on subject
        is_correct = False
        if subject == "MATH":
            is_correct = await solver_client.validate("MATH", settings.MATH_SERVICE_URL, student_attempt, expected_expression)
        else:
            # Fallback text check
            clean_attempt = student_attempt.lower().replace(" ", "")
            clean_expected = expected_expression.lower().replace(" ", "")
            is_correct = (clean_attempt == clean_expected) or (clean_expected in clean_attempt)

        if is_correct:
            next_index = current_index + 1
            if next_index >= len(solved_steps):
                feedback = "Excellent! You have successfully solved the entire problem! Awesome job."
                return {
                    "current_step_index": next_index,
                    "tutor_feedback": feedback,
                    "hint_count": 0
                }
            else:
                next_step_hint = solved_steps[next_index].get("hint", "")
                feedback = f"Spot on! That is correct. Now, what should we do next? (Hint: {next_step_hint})"
                return {
                    "current_step_index": next_index,
                    "tutor_feedback": feedback,
                    "hint_count": 0
                }
        else:
            new_hint_count = state.get("hint_count", 0) + 1
            return {
                "hint_count": new_hint_count,
                "tutor_feedback": "__TRIGGER_HINT__"
            }
    except Exception as e:
        logger.error(f"Error in tutor_loop_node: {e}", exc_info=True)
        return {
            "subject": "GENERAL",
            "solved_steps": [{"step_num": 1, "expression": "GENERAL", "hint": "General fallback due to error."}],
            "current_step_index": 0,
            "tutor_feedback": ""
        }
