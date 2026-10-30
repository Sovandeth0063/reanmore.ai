"""
File: services/science_service/app/solvers/chemistry.py
Description: Elementary Chemistry & Physical Matter solver tailored specifically for Grade 1–3.
             Covers observable states of matter (Solid, Liquid, Gas), phase changes (melting,
             freezing, evaporation, condensation), and everyday mixing/dissolving.
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

ATOMIC_WEIGHTS = {
    "H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999, "Na": 22.990,
    "Cl": 35.45, "Fe": 55.845, "Cu": 63.546, "S": 32.06, "K": 39.098
}


def solve_grade_1_3_matter(expression: str) -> dict:
    """
    Deterministic rule-based solver tailored for Grade 1-3 elementary science:
    - Melting (Ice -> Water)
    - Freezing (Water -> Ice)
    - Evaporating / Boiling (Water -> Steam / Vapor)
    - Condensation (Steam -> Water Droplets)
    - Dissolving (Sugar/Salt in Water)
    - Identifying Solid, Liquid, or Gas
    """
    expr_l = expression.lower()

    # 1. Boiling / Evaporation (Liquid -> Gas)
    if ("water" in expr_l or "liquid" in expr_l) and any(w in expr_l for w in ["heat", "boil", "steam", "vapor", "hot", "evaporat", "kettle"]):
        steps = [
            "💧 Observe: Liquid water gets hot from heat energy.",
            "💨 Change: The water warms up and turns into steam or gas.",
            "🌟 Conclusion: This change is called Evaporation (liquid turns into gas)."
        ]
        return {"solution": "Evaporation (liquid to gas)", "steps": steps, "success": True, "error": None}

    # 2. Melting (Solid -> Liquid)
    if ("ice" in expr_l or "solid" in expr_l or "snow" in expr_l or "popsicle" in expr_l or "butter" in expr_l) and any(w in expr_l for w in ["melt", "warm", "sun", "hot"]):
        steps = [
            "🧊 Observe: Solid ice absorbs heat from the warm air or sun.",
            "💧 Change: The hard ice softens and turns into liquid water.",
            "🌟 Conclusion: This change is called Melting (solid turns into liquid)."
        ]
        return {"solution": "Melting (solid to liquid)", "steps": steps, "success": True, "error": None}

    # 3. Freezing (Liquid -> Solid)
    if ("water" in expr_l or "liquid" in expr_l or "juice" in expr_l) and any(w in expr_l for w in ["freeze", "freezer", "cold", "ice tray", "frost"]):
        steps = [
            "💧 Observe: Liquid water is placed somewhere very cold (freezer).",
            "🧊 Change: The water loses heat and hardens into solid ice.",
            "🌟 Conclusion: This change is called Freezing (liquid turns into solid)."
        ]
        return {"solution": "Freezing (liquid to solid)", "steps": steps, "success": True, "error": None}

    # 4. Condensation (Gas -> Liquid)
    if any(w in expr_l for w in ["condens", "dew", "droplet", "cloud", "foggy mirror", "cold glass", "sweat on glass"]):
        steps = [
            "💨 Observe: Warm water vapor in the air touches a cold surface.",
            "💧 Change: The gas cools down and turns back into tiny water drops.",
            "🌟 Conclusion: This change is called Condensation (gas turns into liquid)."
        ]
        return {"solution": "Condensation (gas to liquid)", "steps": steps, "success": True, "error": None}

    # 5. Dissolving / Mixing (Sugar, Salt in water)
    if any(w in expr_l for w in ["sugar", "salt", "cocoa", "drink mix"]) and any(w in expr_l for w in ["dissolve", "mix", "stir", "water", "disappear"]):
        steps = [
            "🥄 Observe: Solid grains (like sugar or salt) are stirred into liquid water.",
            "✨ Change: The grains break apart into tiny pieces you cannot see.",
            "🌟 Conclusion: The solid has Dissolved into the liquid to form a mixture."
        ]
        return {"solution": "Dissolving in water", "steps": steps, "success": True, "error": None}

    # 6. Identifying 3 States of Matter
    if "solid" in expr_l and any(w in expr_l for w in ["what is", "example", "property", "shape"]):
        steps = [
            "🧱 A solid has a fixed shape (like a wooden block or ice cube).",
            "🤲 You can hold it in your hands and it does not flow.",
            "🌟 Conclusion: Solids keep their own shape!"
        ]
        return {"solution": "Solid (holds its own shape)", "steps": steps, "success": True, "error": None}

    if "liquid" in expr_l and any(w in expr_l for w in ["what is", "example", "property", "shape"]):
        steps = [
            "💧 A liquid flows and takes the shape of whatever cup or bowl it is in.",
            "🌊 Examples include water, milk, and juice.",
            "🌟 Conclusion: Liquids flow and take the shape of their container!"
        ]
        return {"solution": "Liquid (flows and takes container shape)", "steps": steps, "success": True, "error": None}

    if "gas" in expr_l and any(w in expr_l for w in ["what is", "example", "property", "shape"]):
        steps = [
            "💨 A gas spreads out to fill the entire room or container.",
            "🎈 Examples include air in a balloon and steam from a kettle.",
            "🌟 Conclusion: Gases spread out and are often invisible!"
        ]
        return {"solution": "Gas (spreads out to fill space)", "steps": steps, "success": True, "error": None}

    return {"success": False}


def calculate_molar_mass(formula_str: str) -> dict:
    """Auxiliary calculator for chemical formulas (e.g. H2O, NaCl)."""
    clean = re.sub(r'\b(molar\s+mass\s+of|molecular\s+weight\s+of|weight|mass)\b', '', formula_str, flags=re.IGNORECASE).strip()
    steps = [f"Formula: '{clean}'"]
    pattern = re.compile(r'([A-Z][a-z]*)(\d*)')
    matches = pattern.findall(clean)
    if not matches:
        return {"success": False}

    total = 0.0
    for elem, count in matches:
        c = int(count) if count else 1
        if elem in ATOMIC_WEIGHTS:
            w = ATOMIC_WEIGHTS[elem]
            total += c * w
            steps.append(f"{elem}: {c} × {w} = {c * w:.3f} g/mol")
        else:
            return {"success": False}

    if total > 0:
        steps.append(f"Total Molar Mass = {round(total, 2)} g/mol")
        return {"solution": f"{round(total, 2)} g/mol", "steps": steps, "success": True, "error": None}
    return {"success": False}


def solve_chemistry_ai(expression: str, grade_level: str = "grade_1_3") -> dict:
    """
    LLM Step Solver fallback (Gemini).
    Automatically triggered when deterministic rules do not match the input.
    """
    if not GEMINI_API_KEY:
        return {
            "solution": None,
            "steps": [],
            "success": False,
            "error": "Chemistry AI solver unavailable: GEMINI_API_KEY is not configured in Science Service."
        }

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        model = genai.GenerativeModel(model_name)
        prompt = prompt_controller.get_prompt("chemistry", expression, grade_level)
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
        return {"solution": None, "steps": [expression], "success": False, "error": f"Chemistry AI solver failed: {str(e)}"}


def solve_chemistry(expression: str, context: dict = None) -> dict:
    """
    Main chemistry entry point:
    1. Deterministic Grade 1-3 Rule Matcher (Fast path, 0 latency)
    2. Auxiliary Formula Molar Mass
    3. LLM Fallback (Gemini) for arbitrary science questions
    """
    context = context or {}
    grade_level = context.get("grade_level", "grade_1_3")

    # 1. Primary: Elementary States of Matter & Observable Changes (Grade 1-3)
    elem_res = solve_grade_1_3_matter(expression)
    if elem_res.get("success"):
        return elem_res

    # 2. Auxiliary: Molar mass if direct formula entered (e.g. H2O)
    mass_res = calculate_molar_mass(expression)
    if mass_res.get("success"):
        return mass_res

    # 3. LLM Fallback
    return solve_chemistry_ai(expression, grade_level)
