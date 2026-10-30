"""
File: backend/testing/unit/socratic/test_skill_templates.py
Description: Unit tests for the 6 Core Math Skill Templates + 1-step word problem.
             Verifies:
             1. Correct matching by skill_id.
             2. 2-4 milestone decomposition steps.
             3. Non-overlapping numbers in make_distinct_example().
"""

from fractions import Fraction
import pytest
from app.services.socratic.skills import skill_registry


def test_add_within_10_prefers_simple_counting():
    problem = {"op": "+", "a": 2, "b": 2}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "add_within_10"

    steps = skill.build_steps(problem)
    assert len(steps) == 1
    assert steps[0].concept == "count_all"
    assert steps[0].expected_answer == "4"

    # Direct facts ask for the one non-trivial act (the total); they must not
    # ask the child to transcribe an operand that is already on screen.
    text = f"{steps[0].mission} {steps[0].clue} {steps[0].your_turn}".lower()
    assert "first group" not in text and "second group" not in text
    assert "make 10" not in text and "bar model" not in text
    assert steps[0].visual_spec["type"] == "objects"
    assert steps[0].visual_spec["groups"] == [2, 2]

    # The parallel example must be equally simple and use different numbers.
    ex = skill.make_distinct_example(problem)
    assert {2, 4}.isdisjoint({ex["a"], ex["b"], ex["sum"]})


def test_add_within_20_skill():
    problem = {"op": "+", "a": 8, "b": 6}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "add_within_20"

    steps = skill.build_steps(problem)
    assert len(steps) == 2
    assert steps[0].concept == "make_a_ten"
    assert steps[0].expected_answer == "2"  # 10 - 8 = 2
    assert steps[1].expected_answer == "14"  # 8 + 6 = 14

    # Verify distinct example has zero intersection with problem numbers
    ex = skill.make_distinct_example(problem)
    problem_numbers = {8, 6, 14}
    example_numbers = {ex["a"], ex["b"], ex["sum"]}
    assert problem_numbers.isdisjoint(example_numbers)


def test_sub_within_10_uses_simple_take_away():
    problem = {"op": "-", "a": 5, "b": 2}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "sub_within_10"

    steps = skill.build_steps(problem)
    assert len(steps) == 1
    assert steps[0].concept == "count_left"
    assert steps[0].expected_answer == "3"
    assert "start with" not in steps[0].your_turn.lower()
    assert steps[0].visual_spec["type"] == "objects"

    ex = skill.make_distinct_example(problem)
    assert {5, 2, 3}.isdisjoint({ex["a"], ex["b"], ex["answer"]})


def test_one_step_multiplication_word_problem():
    problem = {
        "type": "word_problem",
        "is_word_problem": True,
        "a": 5,
        "b": 8,
        "op": "*",
        "item": "apples",
    }
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "one_step_word_problem"

    steps = skill.build_steps(problem)
    assert len(steps) == 1
    assert steps[0].expected_answer == "40"
    assert steps[0].concept == "repeated_addition"
    assert steps[0].visual_spec["type"] == "array_grid"
    assert steps[0].visual_spec["params"] == {"rows": 5, "cols": 8}
    assert "40" not in " ".join(steps[0].hints)


def test_sub_within_20_skill():
    problem = {"op": "-", "a": 14, "b": 6}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "sub_within_20"

    steps = skill.build_steps(problem)
    assert len(steps) == 2
    assert steps[0].concept == "hop_back_to_ten"
    assert steps[0].expected_answer == "4"  # 14 - 10 = 4
    assert steps[1].expected_answer == "8"  # 14 - 6 = 8

    ex = skill.make_distinct_example(problem)
    problem_numbers = {14, 6, 8}
    example_numbers = {ex["a"], ex["b"], ex["ans"]}
    assert problem_numbers.isdisjoint(example_numbers)


def test_add_2digit_regroup_skill():
    problem = {"op": "+", "a": 15, "b": 27}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "add_2digit_regroup"

    steps = skill.build_steps(problem)
    assert len(steps) == 3
    assert steps[0].concept == "add_ones_column"
    assert steps[0].expected_answer == "12"  # 5 + 7 = 12
    assert steps[1].expected_answer == "2"   # 12 - 10 = 2
    assert steps[2].expected_answer == "42"  # 15 + 27 = 42

    ex = skill.make_distinct_example(problem)
    problem_numbers = {15, 27, 42, 12}
    example_numbers = {ex["a"], ex["b"], ex["total"]}
    assert problem_numbers.isdisjoint(example_numbers)


def test_sub_2digit_borrow_skill():
    problem = {"op": "-", "a": 42, "b": 17}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "sub_2digit_borrow"

    steps = skill.build_steps(problem)
    assert len(steps) == 3
    assert steps[0].concept == "regroup_ten_to_ones"
    assert steps[0].expected_answer == "12"  # 2 + 10 = 12
    assert steps[1].expected_answer == "5"   # 12 - 7 = 5
    assert steps[2].expected_answer == "25"  # 42 - 17 = 25


def test_mult_tables_skill():
    problem = {"op": "*", "a": 4, "b": 3}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "mult_tables"

    steps = skill.build_steps(problem)
    assert len(steps) == 2
    assert steps[0].expected_answer == "3"
    assert steps[1].expected_answer == "12"


def test_fraction_equivalent_skill():
    problem = {"type": "fraction_equivalent", "a": Fraction(2, 4)}
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "fraction_equivalent"

    steps = skill.build_steps(problem)
    assert len(steps) == 2


def test_one_step_word_problem_skill():
    problem = {
        "type": "word_problem",
        "total": 15,
        "part1": 7,
        "op": "-",
        "item": "marbles"
    }
    skill = skill_registry.match(problem)
    assert skill is not None
    assert skill.skill_id == "one_step_word_problem"

    steps = skill.build_steps(problem)
    assert len(steps) == 2
    assert steps[0].expected_answer == "15"
    assert steps[1].expected_answer == "8"
