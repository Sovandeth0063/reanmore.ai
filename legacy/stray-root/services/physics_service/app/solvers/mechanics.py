"""
File: services/physics_service/app/solvers/mechanics.py
Description: Physics mechanics step solver engine. Resolves force and kinematics equations
             deterministically for simple metrics or falls back to AI step compilation
             using Gemini with dynamic prompts.
"""

import re
import json
import os
import google.generativeai as genai
from app.prompts import prompt_controller

# Initialize Gemini safely using environment key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def solve_mechanics_ai(expression: str, grade_level: str) -> dict:
    """
    Compiles physics solver steps using Gemini with grade-level adaptive dynamic prompts.
    """
    if not GEMINI_API_KEY:
        return {
            "solution": None,
            "steps": [expression],
            "success": False,
            "error": "Gemini API key is not configured in the Physics Service environment."
        }
        
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = prompt_controller.get_solver_prompt(expression, grade_level)
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean any accidental markdown block wrappers (e.g. ```json ... ```)
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            
        steps = json.loads(text)
        if isinstance(steps, list) and len(steps) > 0:
            final_sol = steps[-1] # The last step is the final solution
            return {
                "solution": str(final_sol),
                "steps": steps,
                "success": True,
                "error": None
            }
        else:
            raise ValueError("Parsed output is not a valid list of steps.")
    except Exception as e:
        return {
            "solution": None,
            "steps": [expression],
            "success": False,
            "error": f"Physics AI Solver failed: {str(e)}"
        }

def solve_physics(expression: str, context: dict = None) -> dict:
    """
    Main solve routing for Physics Service.
    Determines if it is a force calculation or kinematics calculation and runs it.
    Uses AI solver for flexible natural language processing.
    """
    context = context or {}
    grade_level = context.get("grade_level", "grade_10_12")
    
    # Check for simple force calculation F = ma
    # e.g., "find force for mass 10kg and acceleration 2m/s^2"
    query_lower = expression.lower()
    mass_match = re.search(r'\bmass\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:kg)?', query_lower)
    accel_match = re.search(r'\b(?:acceleration|accel)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:m/s\^2|m/s2)?', query_lower)
    
    if mass_match and accel_match:
        try:
            mass = float(mass_match.group(1))
            accel = float(accel_match.group(1))
            force = mass * accel
            steps = [
                f"Identify mass (m) = {mass} kg",
                f"Identify acceleration (a) = {accel} m/s^2",
                "Apply Newton's Second Law: F = m * a",
                f"Substitute values: F = {mass} * {accel}",
                f"Calculate force: F = {force} N"
            ]
            return {
                "solution": f"{force} N",
                "steps": steps,
                "success": True,
                "error": None
            }
        except Exception:
            pass # Fallback to AI solver if parsing fails
            
    # Fallback to AI-based step compilation
    return solve_mechanics_ai(expression, grade_level)
