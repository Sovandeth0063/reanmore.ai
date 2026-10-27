"""
File: backend/testing/unit/socratic/test_parse_verifier.py
Description: Unit tests for the 7-Stage Word Problem Parse Verification Pipeline.
"""

import pytest
from app.services.socratic.parse_verifier import (
    verify_and_parse_word_problem,
    extract_numbers_from_text,
)


def test_extract_numbers():
    text = "Dara has 15 marbles and gives 7 to Bopha."
    nums = extract_numbers_from_text(text)
    assert len(nums) == 2
    assert nums[0][0] == "15"
    assert nums[1][0] == "7"


def test_subtraction_word_problem_confident():
    text = "Dara has 15 marbles. He gives 7 to Bopha. How many marbles does Dara have left?"
    res = verify_and_parse_word_problem(text, grade_level="grade_1_3")
    assert res.is_valid is True
    assert res.problem_type == "word_problem"
    assert res.parsed_problem["total"] == 15.0
    assert res.parsed_problem["part1"] == 7.0
    assert res.parsed_problem["op"] == "-"
    assert res.parsed_problem["expected_answer"] == "8"
    assert res.needs_confirmation is False


def test_addition_word_problem_confident():
    text = "Chan has 8 books. His sister gives him 6 more books. How many books in all?"
    res = verify_and_parse_word_problem(text, grade_level="grade_1_3")
    assert res.is_valid is True
    assert res.parsed_problem["op"] == "+"
    assert res.parsed_problem["expected_answer"] == "14"
    assert res.needs_confirmation is False


def test_ambiguous_word_problem_triggers_child_confirmation():
    # Multi-number ambiguous question
    text = "Dara has 15 marbles, gives 7 to Bopha, then finds 4 more. How many left?"
    res = verify_and_parse_word_problem(text, grade_level="grade_1_3")
    assert res.is_valid is True
    assert res.needs_confirmation is True
    assert "Did you mean:" in res.confirmation_prompt


def test_unclear_or_insufficient_numbers():
    text = "Hello, can you help me with my math homework?"
    res = verify_and_parse_word_problem(text)
    assert res.is_valid is False
    assert res.problem_type == "unclear"


def test_pure_arithmetic_expressions_are_not_word_problems():
    from app.services.socratic.parse_verifier import is_pure_arithmetic_expression
    
    # Chained addition
    assert is_pure_arithmetic_expression("7 + 3 + 2 + 5 =") is True
    assert is_pure_arithmetic_expression("solve 7 + 3 + 2 + 5 =") is True
    assert is_pure_arithmetic_expression("4 + 5 + 6") is True
    assert is_pure_arithmetic_expression("30 + [ ] = 100") is True

    # Word problems should not be treated as pure arithmetic
    assert is_pure_arithmetic_expression("Dara has 15 marbles and gives 7 to Bopha.") is False
    assert is_pure_arithmetic_expression("Chan has 8 books. His sister gives him 6 more books.") is False

    # verify_and_parse_word_problem should return is_valid=False for pure arithmetic
    res = verify_and_parse_word_problem("7 + 3 + 2 + 5 =")
    assert res.is_valid is False
    assert res.problem_type == "arithmetic"
    assert res.needs_confirmation is False
