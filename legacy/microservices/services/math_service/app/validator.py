"""
File: services/math_service/app/validator.py
Description: Multi-modal math validator handling numeric, fractions, word numbers, 
             unit stripping, and SymPy algebraic equivalence.
"""

import re
from fractions import Fraction
from typing import Optional
from sympy import sympify, simplify

ALLOWED_PATTERN = re.compile(r'^[a-zA-Z0-9\s\+\-\*\/\^\(\)\=\,\.\_\!\%\:\?\'\"\$]*$')

WORD_TO_NUMBER = {
    "zero": 0.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
    "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0,
    "ten": 10.0, "eleven": 11.0, "twelve": 12.0, "half": 0.5,
    "one half": 0.5, "quarter": 0.25, "one quarter": 0.25,
    "three quarters": 0.75, "third": 1.0 / 3.0, "one third": 1.0 / 3.0
}


def validate_expression(expr: str) -> bool:
    """
    Validates if an expression contains only safe characters/words for mathematical parsing.
    """
    if not expr or len(expr.strip()) == 0:
        return False
    return bool(ALLOWED_PATTERN.match(expr))


def parse_numeric_or_fraction(text: str) -> Optional[float]:
    """Extracts a numeric float value from digits, fractions, or word-numbers."""
    clean = text.lower().strip()
    
    if clean in WORD_TO_NUMBER:
        return WORD_TO_NUMBER[clean]

    # Clean off trailing unit nouns (e.g. "5 apples" -> "5", "10 cm" -> "10", "3 metres" -> "3")
    clean = re.sub(r'^(about|approx|around|=|\s)+', '', clean)
    clean = re.sub(r'\s*(cookies|apples|candies|cm|m|km|kg|g|dollars|\$|units|hours|mins|seconds|metres|meters).*$', '', clean).strip()

    # Try standard fraction e.g. "1/2", "3/4"
    if "/" in clean:
        parts = clean.split("/")
        if len(parts) == 2:
            try:
                num = float(parts[0].strip())    # -> 3.0 (Numerator)
                denom = float(parts[1].strip())  # -> 4.0 (Denominator)
                if denom != 0:
                    return num / denom
            except ValueError:
                pass

    # Try pure float / int
    try:
        return float(clean)
    except ValueError:
        pass

    # Regex search for first standalone number
    match = re.search(r'[-+]?\d*\.?\d+', clean)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            pass

    return None


def verify_equivalence(student_input: str, expected_step: str) -> bool:
    """
    Compares two mathematical/algebraic steps to see if they represent equivalent statements.
    Handles:
      1. Exact string matches
      2. Numerical and fraction values (with 0.01 tolerance)
      3. Word numbers ("five" vs "5", "half" vs "1/2")
      4. SymPy symbolic algebraic equations
    """
    if not student_input or not expected_step:
        return False

    s_clean = student_input.strip().lower()
    e_clean = expected_step.strip().lower()

    if s_clean == e_clean:
        return True

    # 1. Numeric / Fraction / Unit Equivalence Check
    s_val = parse_numeric_or_fraction(s_clean)
    e_val = parse_numeric_or_fraction(e_clean)

    if s_val is not None and e_val is not None: # Ensures both inputs were successfully parsed into numbers.
        if abs(s_val - e_val) < 0.01:
            return True

    # 2. SymPy Symbolic Algebraic Equivalence
    try:
        def to_zero_expr(eq_str: str):
            eq_str = eq_str.replace('^', '**').replace('==', '=')
            if '=' in eq_str:
                parts = [p.strip() for p in eq_str.split('=', 1)]
                if len(parts) == 2:
                    return sympify(parts[0]) - sympify(parts[1])
            return sympify(eq_str.strip())

        student_expr = to_zero_expr(student_input)
        expected_expr = to_zero_expr(expected_step)

        # 2a. Direct difference is 0
        diff = simplify(student_expr - expected_expr)
        if diff == 0:
            return True

        # 2b. Scale factor equivalence for algebraic expressions (e.g. 3*x - 9 = 0 vs x - 3 = 0)
        if student_expr.free_symbols and expected_expr.free_symbols:
            ratio = simplify(student_expr / expected_expr)
            if ratio.is_constant() and ratio != 0:
                return True
    except Exception:
        pass

    return False
