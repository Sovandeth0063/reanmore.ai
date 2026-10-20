"""
File: orchestrator/app/services/socratic/math_engine/cas.py
Description: In-process exact CAS (Computer Algebra System) and arithmetic engine.
             Provides symbolic equivalence, exact Fraction arithmetic, AST safety,
             and zero-mock mathematical validation for elementary mathematics (Grades 1-6).
"""

import ast
import re
import logging
from fractions import Fraction
from typing import Optional, Tuple, Dict, Any, Union
import sympy

from app.services.socratic.safe_math import safe_eval_ast

logger = logging.getLogger("orchestrator.socratic.math_engine.cas")

MAX_MAGNITUDE = 10_000_000


def format_exact_fraction(val: Fraction) -> str:
    """Formats a Fraction as an elementary-friendly string (integer, clean decimal, or fraction)."""
    if val.denominator == 1:
        return str(val.numerator)
    # Check if decimal terminates nicely (e.g. 1/2 -> 0.5, 3/4 -> 0.75)
    denom = val.denominator
    for factor in (2, 5):
        while denom % factor == 0:
            denom //= factor
    if denom == 1:
        dec = float(val)
        return f"{dec:.6f}".rstrip("0").rstrip(".")
    return f"{val.numerator}/{val.denominator}"


def evaluate_exact(expression: str) -> Optional[Fraction]:
    """
    Safely evaluates an arithmetic expression into an exact Fraction.
    Uses AST-based evaluator first, with SymPy fallback for extended expressions.
    """
    if not expression or not expression.strip():
        return None

    # Try fast AST evaluation first
    res = safe_eval_ast(expression)
    if res is not None:
        return res

    # SymPy safe fallback
    try:
        clean = (
            expression
            .replace("×", "*")
            .replace("÷", "/")
            .replace("x", "*")
            .replace("^", "**")
            .strip()
        )
        clean = re.sub(r"=.*$", "", clean).strip()

        # Disallow dangerous builtins or calls
        if any(bad in clean for bad in ["__", "import", "eval", "exec", "open", "os", "sys"]):
            return None

        sym_res = sympy.sympify(clean, evaluate=True)
        if isinstance(sym_res, (sympy.Integer, sympy.Rational)):
            return Fraction(int(sym_res.p), int(sym_res.q))
        elif isinstance(sym_res, sympy.Float):
            return Fraction(str(float(sym_res)))
    except Exception as e:
        logger.debug(f"[CAS] evaluate_exact failed on '{expression}': {e}")
    return None


def is_mathematically_equivalent(student_input: str, target_answer: str) -> bool:
    """
    Determines whether a student's input is mathematically equivalent to the target answer.
    Handles:
    - Exact arithmetic equivalence: '0.5' == '1/2' == '2/4'
    - Integer equivalence: '14' == '14.0' == '10 + 4'
    - Algebraic symbolic equivalence: '2 + x' == 'x + 2'
    """
    if not student_input or not target_answer:
        return False

    s_clean = student_input.strip()
    t_clean = target_answer.strip()

    # Direct literal match
    if s_clean.lower() == t_clean.lower():
        return True

    # 1. Exact Numerical / Fraction check
    s_val = evaluate_exact(s_clean)
    t_val = evaluate_exact(t_clean)
    if s_val is not None and t_val is not None:
        return s_val == t_val

    # 2. SymPy Symbolic check (for algebra or expressions with variables)
    try:
        s_expr = sympy.sympify(s_clean.replace("×", "*").replace("÷", "/"))
        t_expr = sympy.sympify(t_clean.replace("×", "*").replace("÷", "/"))
        diff = sympy.simplify(s_expr - t_expr)
        return diff == 0
    except Exception:
        pass

    return False


def parse_binary_arithmetic(query: str) -> Optional[Dict[str, Any]]:
    """
    Detects and parses two-operand elementary arithmetic expressions (+, -, *, /).
    Returns dict with a, b, op, and exact answer if matched.
    """
    clean = (
        query
        .replace("×", "*")
        .replace("÷", "/")
        .replace("x", "*")
        .replace("plus", "+")
        .replace("minus", "-")
        .replace("times", "*")
        .strip()
    )
    # Match standard patterns like '8 + 6', '15 + 27', '14 - 6', '4 * 3', '24 / 6'
    match = re.search(r"^\s*(\d+(?:\.\d+)?|\d+/\d+)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?|\d+/\d+)\s*(?:=\s*\??)?\s*$", clean)
    if not match:
        return None

    a_str, op, b_str = match.group(1), match.group(2), match.group(3)
    a_val = evaluate_exact(a_str)
    b_val = evaluate_exact(b_str)

    if a_val is None or b_val is None:
        return None

    ans: Optional[Fraction] = None
    if op == "+":
        ans = a_val + b_val
    elif op == "-":
        ans = a_val - b_val
    elif op == "*":
        ans = a_val * b_val
    elif op == "/":
        if b_val == 0:
            return None
        ans = a_val / b_val

    if ans is None:
        return None

    return {
        "a": a_val,
        "a_str": format_exact_fraction(a_val),
        "b": b_val,
        "b_str": format_exact_fraction(b_val),
        "op": op,
        "answer": ans,
        "answer_str": format_exact_fraction(ans)
    }
