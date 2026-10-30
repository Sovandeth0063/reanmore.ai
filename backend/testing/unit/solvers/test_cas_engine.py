"""
File: backend/testing/unit/solvers/test_cas_engine.py
Description: Unit tests for the in-process SymPy CAS engine (evaluate_exact, equivalence, parsing).
"""

from fractions import Fraction
import pytest
from app.services.socratic.math_engine.cas import (
    evaluate_exact,
    is_mathematically_equivalent,
    format_exact_fraction,
    parse_binary_arithmetic,
)


def test_evaluate_exact_arithmetic():
    assert evaluate_exact("15 + 27") == Fraction(42, 1)
    assert evaluate_exact("14 - 6") == Fraction(8, 1)
    assert evaluate_exact("4 * 3") == Fraction(12, 1)
    assert evaluate_exact("24 / 6") == Fraction(4, 1)
    assert evaluate_exact("1/2 + 1/4") == Fraction(3, 4)
    assert evaluate_exact("0.5") == Fraction(1, 2)
    assert evaluate_exact("10.5 - 2.5") == Fraction(8, 1)


def test_evaluate_exact_safety_rejections():
    # Rejects syntax errors or dangerous tokens
    assert evaluate_exact("__import__('os')") is None
    assert evaluate_exact("open('/etc/passwd')") is None
    assert evaluate_exact("") is None


def test_is_mathematically_equivalent():
    # Fractions & Decimals
    assert is_mathematically_equivalent("1/2", "0.5") is True
    assert is_mathematically_equivalent("2/4", "1/2") is True
    assert is_mathematically_equivalent("3/6", "0.5") is True
    assert is_mathematically_equivalent("0.75", "3/4") is True

    # Integers with spacing and operators
    assert is_mathematically_equivalent("14", "14.0") is True
    assert is_mathematically_equivalent("10 + 4", "14") is True
    assert is_mathematically_equivalent("15 - 1", "14") is True

    # Algebraic commutativity
    assert is_mathematically_equivalent("x + 2", "2 + x") is True
    assert is_mathematically_equivalent("2 * x", "x * 2") is True

    # Non-equivalent checks
    assert is_mathematically_equivalent("14", "15") is False
    assert is_mathematically_equivalent("1/2", "1/3") is False


def test_format_exact_fraction():
    assert format_exact_fraction(Fraction(4, 1)) == "4"
    assert format_exact_fraction(Fraction(1, 2)) == "0.5"
    assert format_exact_fraction(Fraction(3, 4)) == "0.75"
    assert format_exact_fraction(Fraction(1, 3)) == "1/3"


def test_parse_binary_arithmetic():
    res = parse_binary_arithmetic("8 + 6 = ?")
    assert res is not None
    assert res["op"] == "+"
    assert res["a"] == Fraction(8, 1)
    assert res["b"] == Fraction(6, 1)
    assert res["answer"] == Fraction(14, 1)

    res_sub = parse_binary_arithmetic("42 - 17")
    assert res_sub is not None
    assert res_sub["op"] == "-"
    assert res_sub["answer"] == Fraction(25, 1)

    res_mult = parse_binary_arithmetic("4 × 3")
    assert res_mult is not None
    assert res_mult["op"] == "*"
    assert res_mult["answer"] == Fraction(12, 1)


def test_parse_binary_arithmetic_conversational_wrappers():
    res = parse_binary_arithmetic("what 2+2")
    assert res is not None
    assert res["answer"] == Fraction(4, 1)

    res_apostrophe = parse_binary_arithmetic("what's 8 + 6?")
    assert res_apostrophe is not None
    assert res_apostrophe["answer"] == Fraction(14, 1)

    res_no_apostrophe = parse_binary_arithmetic("whats 6 x 7")
    assert res_no_apostrophe is not None
    assert res_no_apostrophe["op"] == "*"
    assert res_no_apostrophe["answer"] == Fraction(42, 1)

    res_please = parse_binary_arithmetic("please solve 9 - 4")
    assert res_please is not None
    assert res_please["answer"] == Fraction(5, 1)

    # Narrative text must still be rejected.
    assert parse_binary_arithmetic("Dara has 2 apples and 2 more.") is None
