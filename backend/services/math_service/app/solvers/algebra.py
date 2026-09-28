"""
File: services/math_service/app/solvers/algebra.py
Description: Decomposes elementary math queries (arithmetic, fractions, word problems, algebra)
             into 2-4 verified pedagogical steps.
"""

import ast
import re
import json
import os
from fractions import Fraction
import google.generativeai as genai

try:
    from app.prompts import prompt_controller
except ImportError:
    from services.math_service.app.prompts import prompt_controller

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    decimal = float(value)
    denominator = value.denominator
    for factor in (2, 5):
        while denominator % factor == 0:
            denominator //= factor
    if denominator == 1:
        return f"{decimal:.10f}".rstrip("0").rstrip(".")
    return f"{value.numerator}/{value.denominator}"


def _evaluate_numeric_expression(expression: str) -> Fraction:
    """Evaluate a numeric expression using only arithmetic AST nodes."""
    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST) -> Fraction:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Fraction(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left = visit(node.left)
            right = visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        raise ValueError("Expression contains unsupported syntax")

    return visit(tree)


def decompose_arithmetic(expr: str) -> dict:
    """Deterministic 2-3 step decomposition for basic arithmetic operations (+, -, *, /)."""
    clean = expr.replace("×", "*").replace("÷", "/").replace("x", "*")
    if len(re.findall(r"[+\-*/]", clean)) > 1 and not re.search(r"[A-Za-z]", clean):
        try:
            result = _evaluate_numeric_expression(clean)
            answer = _format_fraction(result)
            return {
                "solution": answer,
                "steps": ["Read the complete arithmetic expression.", f"Calculate the expression to get {answer}."],
                "structured_steps": [
                    {"step_number": 1, "title": "Read the Expression", "clue": "Use the numbers and operations in order.", "expected_answer": clean.strip()},
                    {"step_number": 2, "title": "Calculate", "clue": f"Evaluate the expression: {clean.strip()}", "expected_answer": answer},
                ],
                "success": True,
                "error": None,
            }
        except (SyntaxError, ValueError, ZeroDivisionError) as error:
            return {"success": False, "error": str(error)}
    match = re.search(r'(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)', clean)
    if not match:
        return {"success": False}

    a, op, b = Fraction(match.group(1)), match.group(2), Fraction(match.group(3))
    a_str = _format_fraction(a)
    b_str = _format_fraction(b)

    if op == '+':
        ans = a + b
        ans_str = _format_fraction(ans)
        steps = [
            {"step_number": 1, "title": "Identify the Numbers", "clue": f"We are adding {a_str} and {b_str}.", "expected_answer": a_str},
            {"step_number": 2, "title": "Perform Addition", "clue": f"Calculate {a_str} + {b_str}.", "expected_answer": ans_str}
        ]
    elif op == '-':
        ans = a - b
        ans_str = _format_fraction(ans)
        steps = [
            {"step_number": 1, "title": "Identify Starting Value", "clue": f"We start with {a_str} and take away {b_str}.", "expected_answer": a_str},
            {"step_number": 2, "title": "Perform Subtraction", "clue": f"Calculate {a_str} - {b_str}.", "expected_answer": ans_str}
        ]
    elif op == '*':
        ans = a * b
        ans_str = _format_fraction(ans)
        steps = [
            {"step_number": 1, "title": "Identify Groups", "clue": f"We have {a_str} groups of {b_str}.", "expected_answer": a_str},
            {"step_number": 2, "title": "Multiply", "clue": f"Multiply {a_str} × {b_str}.", "expected_answer": ans_str}
        ]
    else:
        if b == 0:
            return {"success": False, "error": "Division by zero"}
        ans = a / b
        ans_str = _format_fraction(ans)
        steps = [
            {"step_number": 1, "title": "Set Up Division", "clue": f"How many times does {b_str} fit into {a_str}?", "expected_answer": b_str},
            {"step_number": 2, "title": "Divide", "clue": f"Calculate {a_str} ÷ {b_str}.", "expected_answer": ans_str}
        ]

    return {
        "solution": ans_str,
        "steps": [s["clue"] for s in steps],
        "structured_steps": steps,
        "success": True,
        "error": None
    }


def is_word_problem(expression: str) -> bool:
    """Checks if the expression contains plain english words that indicate a word problem."""
    words = re.findall(r'\b[a-zA-Z]{2,}\b', expression)
    math_terms = {'sin', 'cos', 'tan', 'log', 'ln', 'sqrt', 'exp', 'pi', 'solve', 'for', 'evaluate', 'simplify'}
    words = [w for w in words if w.lower() not in math_terms]
    return len(words) > 1


def solve_math_ai(expression: str, grade_level: str) -> dict:
    """Compiles math solver steps using Gemini with grade-level adaptive dynamic prompts."""
    if not GEMINI_API_KEY:
        nums = re.findall(r'\d+', expression)
        if len(nums) >= 2:
            n1, n2 = int(nums[0]), int(nums[1])
            expr_lower = expression.lower()
            if any(w in expr_lower for w in ["times", "each", "groups of", "multiply", "multiplied"]):
                res = n1 * n2
                op_name = "multiplication"
            elif any(w in expr_lower for w in ["divided", "split", "share", "shared equally", "divide"]):
                big, small = max(n1, n2), min(n1, n2)
                if small <= 0:
                    return {
                        "solution": None,
                        "steps": [expression],
                        "success": False,
                        "error": "Division by zero",
                    }
                res = Fraction(big, small)
                op_name = "division"
            elif any(w in expr_lower for w in ["total", "together", "plus", "add", "altogether", "combined"]):
                res = n1 + n2
                op_name = "addition"
            else:
                res = max(n1, n2) - min(n1, n2)
                op_name = "subtraction"

            steps = [
                f"Identify the given quantities: {n1} and {n2}",
                f"Determine the operation ({op_name}) from the story problem",
                f"Calculate the final result: {_format_fraction(res)}"
            ]
            return {
                "solution": _format_fraction(res),
                "steps": steps,
                "structured_steps": [
                    {"step_number": 1, "title": "Extract Given Values", "clue": f"Identify {n1} and {n2}", "expected_answer": str(n1)},
                    {"step_number": 2, "title": "Solve Problem", "clue": "Calculate the answer", "expected_answer": _format_fraction(res)}
                ],
                "success": True,
                "error": None
            }
        return {
            "solution": None,
            "steps": [expression],
            "success": False,
            "error": "Gemini API key is not configured in the Math Service environment."
        }

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        model = genai.GenerativeModel(model_name)
        prompt = prompt_controller.get_solver_prompt(expression, grade_level)
        response = model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1].startswith("```"): lines = lines[:-1]
            text = "\n".join(lines).strip()

        steps = json.loads(text)
        if isinstance(steps, list) and len(steps) > 0:
            return {
                "solution": str(steps[-1]),
                "steps": steps,
                "success": True,
                "error": None
            }
        raise ValueError("Parsed output is not a valid list of steps.")
    except Exception as e:
        return {
            "solution": None,
            "steps": [expression],
            "success": False,
            "error": f"AI Step Solver failed: {str(e)}"
        }


def solve_math(expression: str, context: dict = None) -> dict:
    """Main solve entry point for math queries."""
    context = context or {}
    grade_level = context.get("grade_level", "grade_1_3")

    # 1. Deterministic arithmetic
    arith_res = decompose_arithmetic(expression)
    if arith_res.get("success"):
        return arith_res

    # 2. Word problem / AI solver
    return solve_math_ai(expression, grade_level)
