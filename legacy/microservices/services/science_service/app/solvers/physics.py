"""
File: services/science_service/app/solvers/physics.py
Description: Physics solver module tailored for Grade 1–3 early elementary science
             (Push/Pull forces, gravity, simple motion, observable magnets & light).
             Includes robust LLM fallback (Gemini) when deterministic rules do not match.
"""

import re
import json
import os
import google.generativeai as genai

try:
    from app.prompts.controller import prompt_controller
except ImportError:
    from services.science_service.app.prompts.controller import prompt_controller

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def solve_grade_1_3_physics(expression: str) -> dict:
    """
    Deterministic rule-based solver for Grade 1-3 elementary physics:
    - Push and Pull forces (movement, stopping, speeding up)
    - Gravity (things falling down to the ground)
    - Friction (rubbing hands, rough vs smooth slides)
    - Magnets (attract / stick vs repel / push away)
    - Light & Shadows (shadows form when light is blocked)
    """
    expr_l = expression.lower()

    # 1. Gravity (Falling down)
    if any(w in expr_l for w in ["gravity", "fall", "drop", "dropped", "downward", "down to earth", "toss up"]):
        steps = [
            "🍎 Observe: When you let go of an object, it falls downward towards the ground.",
            "🌍 Cause: Earth has an invisible pulling force called Gravity.",
            "🌟 Conclusion: Gravity pulls all objects down toward the ground!"
        ]
        return {"solution": "Gravity pulls objects downward", "steps": steps, "success": True, "error": None}

    # 2. Push vs Pull Forces
    if "push" in expr_l or "pull" in expr_l or "move a toy" in expr_l or "force" in expr_l:
        steps = [
            "🚀 Observe: Objects cannot move by themselves; they need an action.",
            "🤲 Action: A push moves something away from you; a pull brings it closer.",
            "🌟 Conclusion: Pushes and pulls are Forces that make things move, speed up, or stop!"
        ]
        return {"solution": "Pushes and pulls are forces that move objects", "steps": steps, "success": True, "error": None}

    # 3. Friction (Rough vs Smooth)
    if any(w in expr_l for w in ["friction", "slide", "rough", "smooth", "slow down", "rub hands"]):
        steps = [
            "🛝 Observe: A toy car slows down when rolling across a rough carpet.",
            "✋ Cause: Two surfaces rubbing against each other create Friction.",
            "🌟 Conclusion: Friction is a force that slows down moving objects!"
        ]
        return {"solution": "Friction slows down moving objects", "steps": steps, "success": True, "error": None}

    # 4. Magnets
    if any(w in expr_l for w in ["magnet", "magnetic", "attract", "repel", "stick to fridge"]):
        steps = [
            "🧲 Observe: Magnets can pull certain metal objects (like iron clips) without touching them.",
            "⚡ Property: Opposite magnetic poles attract (stick), while like poles push apart.",
            "🌟 Conclusion: Magnets use magnetic force to attract magnetic metals!"
        ]
        return {"solution": "Magnets attract magnetic metals", "steps": steps, "success": True, "error": None}

    # 5. Shadows & Light
    if any(w in expr_l for w in ["shadow", "light", "sunlight", "beam", "dark shape"]):
        steps = [
            "🔦 Observe: Light travels in straight lines from a lamp or the sun.",
            "👤 Cause: When a solid object blocks the path of light, a dark shape appears behind it.",
            "🌟 Conclusion: Shadows are created when light is blocked by an object!"
        ]
        return {"solution": "Shadows form when light is blocked", "steps": steps, "success": True, "error": None}

    return {"success": False}


def solve_physics_ai(expression: str, grade_level: str = "grade_1_3") -> dict:
    """
    LLM Step Solver fallback (Gemini).
    Automatically triggered when deterministic regex rules do not match the input.
    """
    if not GEMINI_API_KEY:
        return {
            "solution": None,
            "steps": [],
            "success": False,
            "error": "Physics AI solver unavailable: GEMINI_API_KEY is not configured in Science Service."
        }

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        model = genai.GenerativeModel(model_name)
        prompt = prompt_controller.get_prompt("physics", expression, grade_level)
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1].startswith("```"): lines = lines[:-1]
            text = "\n".join(lines).strip()
        steps = json.loads(text)
        if isinstance(steps, list) and len(steps) > 0:
            return {"solution": str(steps[-1]), "steps": steps, "success": True, "error": None}
        return {"solution": text, "steps": [text], "success": True, "error": None}
    except Exception as e:
        return {"solution": None, "steps": [expression], "success": False, "error": f"Physics AI solver failed: {str(e)}"}


def solve_physics(expression: str, context: dict = None) -> dict:
    """
    Main physics entry point:
    1. Deterministic Grade 1-3 Rule Matcher (Fast path, 0 latency)
    2. Numerical Mechanics (F=ma)
    3. LLM Fallback (Gemini) for any other queries or complex wording
    """
    context = context or {}
    grade_level = context.get("grade_level", "grade_1_3")

    # 1. Primary: Elementary Grade 1-3 Observable Physics
    elem_res = solve_grade_1_3_physics(expression)
    if elem_res.get("success"):
        return elem_res

    # 2. Auxiliary: Calculation (F=ma) if numerical mass and accel provided
    query_lower = expression.lower()
    mass_match = re.search(r'\bmass\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:kg)?', query_lower)
    accel_match = re.search(r'\b(?:acceleration|accel)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:m/s\^2|m/s2)?', query_lower)
    if mass_match and accel_match:
        try:
            mass = float(mass_match.group(1))
            accel = float(accel_match.group(1))
            force = round(mass * accel, 2)
            steps = [
                f"Identify mass (m) = {mass} kg",
                f"Identify acceleration (a) = {accel} m/s^2",
                "Apply Newton's Second Law: Force = mass × acceleration",
                f"Calculate force: F = {mass} × {accel} = {force} N"
            ]
            return {"solution": f"{force} N", "steps": steps, "success": True, "error": None}
        except Exception:
            pass

    # 3. Fallback to LLM
    return solve_physics_ai(expression, grade_level)
