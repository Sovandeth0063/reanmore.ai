"""
File: services/science_service/app/solvers/biology.py
Description: Biology solver module tailored for Grade 1–3 early elementary science
             (Living vs non-living, plant needs, animal habitats, life cycles, senses).
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


def solve_grade_1_3_biology(expression: str) -> dict:
    """
    Deterministic rule-based solver for Grade 1-3 elementary biology:
    - What plants need to grow (sunlight, water, soil, air)
    - Living vs Non-living things
    - Animal habitats (ocean, jungle, desert, arctic)
    - Life cycles (butterfly caterpillar, frog tadpole, plant seed)
    """
    expr_l = expression.lower()

    # 1. Plants and Photosynthesis (Elementary Needs)
    if "plant" in expr_l and any(w in expr_l for w in ["grow", "need", "sunlight", "water", "food", "photosynthesis", "leaf", "root"]):
        steps = [
            "🌱 Observe: A young green plant needs energy to grow big and strong.",
            "☀️ Needs: Roots drink water from soil, and green leaves catch warm sunlight and air.",
            "🌟 Conclusion: Plants use sunlight, water, and air to make their own food (Photosynthesis)!"
        ]
        return {
            "solution": "Plants make food (Glucose) and oxygen from sunlight, water, and air",
            "steps": steps,
            "success": True,
            "error": None
        }

    # 2. Living vs Non-Living
    if any(w in expr_l for w in ["living", "non-living", "nonliving", "alive", "is a rock living"]):
        steps = [
            "🐶 Living Things: Need food, water, and air to grow and reproduce (like puppies and trees).",
            "🪨 Non-Living Things: Do not grow, breathe, or eat (like rocks, toys, and chairs).",
            "🌟 Conclusion: Living things grow and need food/water, while non-living things do not!"
        ]
        return {
            "solution": "Living things breathe, eat, and grow",
            "steps": steps,
            "success": True,
            "error": None
        }

    # 3. Animal Habitats
    if any(w in expr_l for w in ["habitat", "where do animals live", "ocean", "desert", "arctic", "forest", "jungle"]):
        steps = [
            "🏡 Observe: Animals live in environments that provide food, water, and shelter.",
            "🌍 Examples: Fish live in oceans, camels in warm deserts, and polar bears on cold arctic ice.",
            "🌟 Conclusion: An animal's natural home is called its Habitat!"
        ]
        return {
            "solution": "A habitat is an animal's natural home",
            "steps": steps,
            "success": True,
            "error": None
        }

    # 4. Life Cycles (Frog, Butterfly, Seed)
    if any(w in expr_l for w in ["life cycle", "butterfly", "caterpillar", "tadpole", "frog", "seed"]):
        steps = [
            "🐛 Stage 1: Living things start as eggs or tiny seeds.",
            "🦋 Stage 2: They grow and transform (like a caterpillar into a butterfly, or tadpole into a frog).",
            "🌟 Conclusion: The stages of growth from baby to adult are called a Life Cycle!"
        ]
        return {
            "solution": "Life cycles describe how living things grow and change",
            "steps": steps,
            "success": True,
            "error": None
        }

    return {"success": False}


def solve_biology_ai(expression: str, grade_level: str = "grade_1_3") -> dict:
    """
    LLM Step Solver fallback (Gemini).
    Automatically triggered when deterministic rules do not match the input.
    """
    if not GEMINI_API_KEY:
        return {
            "solution": None,
            "steps": [],
            "success": False,
            "error": "Biology AI solver unavailable: GEMINI_API_KEY is not configured in Science Service."
        }

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        model = genai.GenerativeModel(model_name)
        prompt = prompt_controller.get_prompt("biology", expression, grade_level)
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
        return {"solution": None, "steps": [expression], "success": False, "error": f"Biology AI solver failed: {str(e)}"}


def solve_biology(expression: str, context: dict = None) -> dict:
    """
    Main biology entry point:
    1. Deterministic Grade 1-3 Rule Matcher (Fast path, 0 latency)
    2. LLM Fallback (Gemini) for any other queries
    """
    context = context or {}
    grade_level = context.get("grade_level", "grade_1_3")

    # 1. Primary: Elementary Grade 1-3 Observable Biology
    elem_res = solve_grade_1_3_biology(expression)
    if elem_res.get("success"):
        return elem_res

    # 2. LLM Fallback
    return solve_biology_ai(expression, grade_level)
