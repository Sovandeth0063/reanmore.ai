"""
File: services/math_service/app/validator.py
Description: Mathematical expression sanitizers and algebraic statement equivalence checker using SymPy.
"""

import re
from sympy import sympify, simplify, symbols, Eq

ALLOWED_PATTERN = re.compile(r'^[a-zA-Z0-9\s\+\-\*\/\^\(\)\=\,\.\_\!]*$')

def validate_expression(expr: str) -> bool:
    """
    Validates if an expression contains only safe characters/words for mathematical parsing.
    """
    if not expr or len(expr.strip()) == 0:
        return False
    return bool(ALLOWED_PATTERN.match(expr))

def verify_equivalence(student_input: str, expected_step: str) -> bool:
    """
    Compares two algebraic steps to see if they represent mathematically equivalent statements.
    Examples:
      - '3*x = 9' vs 'x = 3' -> True
      - '3*x - 9 = 0' vs '3*x = 9' -> True
      - 'x^2 = 4' vs 'x^2 - 4 = 0' -> True
    """
    try:
        def to_zero_expr(eq_str: str):
            # Standardize notation
            eq_str = eq_str.replace('^', '**')
            if '=' in eq_str:
                lhs_str, rhs_str = eq_str.split('=')
                return sympify(lhs_str.strip()) - sympify(rhs_str.strip())
            return sympify(eq_str.strip())

        student_expr = to_zero_expr(student_input)
        expected_expr = to_zero_expr(expected_step)

        # 1. Check direct equivalence (difference is 0)
        diff = simplify(student_expr - expected_expr)
        if diff == 0:
            return True

        # 2. Check scale factor equivalence (e.g. 3*x - 9 = 0 vs x - 3 = 0)
        ratio = simplify(student_expr / expected_expr)
        if ratio.is_constant() and ratio != 0:
            return True

        return False
    except Exception:
        return False
