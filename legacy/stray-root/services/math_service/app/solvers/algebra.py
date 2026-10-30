"""
File: services/math_service/app/solvers/algebra.py
Description: Mathematical equation and expression step solver engine.
             Combines SymPy equation solving with dynamic AI step generation
             using Gemini when facing word problems or parsing failures.
"""

import re
import json
import os
import google.generativeai as genai
from sympy import symbols, solve, sympify, Eq
from app.prompts import prompt_controller

# Initialize Gemini safely using environment key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def is_word_problem(expression: str) -> bool:
    """
    Checks if the expression contains plain english words that indicate a word problem,
    rather than just standard equation expressions.
    """
    words = re.findall(r'\b[a-zA-Z]{2,}\b', expression)
    # Filter out common math symbols/functions
    math_terms = {'sin', 'cos', 'tan', 'log', 'ln', 'sqrt', 'exp', 'pi', 'solve', 'for', 'evaluate', 'simplify'}
    words = [w for w in words if w.lower() not in math_terms]
    return len(words) > 1

def solve_math_ai(expression: str, grade_level: str) -> dict:
    """
    Compiles math solver steps using Gemini with grade-level adaptive dynamic prompts.
    """
    if not GEMINI_API_KEY:
        return {
            "solution": None,
            "steps": [expression],
            "success": False,
            "error": "Gemini API key is not configured in the Math Service environment. Cannot parse word problem."
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
            "error": f"AI Step Solver failed: {str(e)}"
        }

def solve_math(expression: str, context: dict = None):
    """
    Main solve routing. Runs deterministic SymPy first if it's a pure equation.
    If it is a word problem, or if SymPy fails, falls back to solve_math_ai.
    """
    context = context or {}
    grade_level = context.get("grade_level", "grade_10_12")

    # If it contains word problem elements, go straight to AI solver
    if is_word_problem(expression):
        return solve_math_ai(expression, grade_level)

    # Standardize exponential notation
    clean_expr = expression.replace('^', '**')
    
    # Simple regex to strip helper words like "solve", "for x", "evaluate", etc.
    clean_expr = re.sub(r'\b(solve|evaluate|simplify|for\s+[a-zA-Z])\b', '', clean_expr, flags=re.IGNORECASE).strip()
    
    # Extract variables (single letters)
    vars_found = sorted(list(set(re.findall(r'\b[a-zA-Z]\b', clean_expr))))
    common_funcs = {'sin', 'cos', 'tan', 'log', 'ln', 'sqrt', 'exp', 'pi', 'e', 'i'}
    vars_found = [v for v in vars_found if v.lower() not in common_funcs]
    
    var_name = vars_found[0] if vars_found else 'x'
    var = symbols(var_name)
    
    steps = [
        f"Original query: '{expression}'",
        f"Cleaned expression: '{clean_expr}'",
        f"Selected target variable: '{var_name}'"
    ]
    
    try:
        if '=' in clean_expr:
            parts = clean_expr.split('=')
            lhs_str = parts[0].strip()
            rhs_str = parts[1].strip()
            
            lhs = sympify(lhs_str)
            rhs = sympify(rhs_str)
            
            steps.append(f"Formulate equation: {lhs} = {rhs}")
            equation = Eq(lhs, rhs)
            solution = solve(equation, var)
            steps.append(f"Subtracted RHS from LHS to get: {lhs - rhs} = 0")
            steps.append(f"Solved equation for {var_name}: {solution}")
            return {
                "solution": str(solution),
                "steps": steps,
                "success": True,
                "error": None
            }
        else:
            expr = sympify(clean_expr)
            solution = solve(expr, var)
            steps.append(f"Solved expression equal to 0 for {var_name}: {solution}")
            return {
                "solution": str(solution),
                "steps": steps,
                "success": True,
                "error": None
            }
    except Exception as e:
        # Fallback to AI Solver if SymPy fails
        return solve_math_ai(expression, grade_level)
