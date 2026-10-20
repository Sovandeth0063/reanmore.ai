"""
File: backend/testing/unit/socratic/test_visual_spec.py
Description: Unit tests for deterministic VisualSpec builders and visual leak checking.
             Verifies Architecture v2.1 Section 8.
"""

import pytest
from app.services.visuals import (
    VisualType,
    VisualMode,
    build_ten_frame,
    build_number_line,
    build_base_ten_blocks,
    build_array_grid,
    build_fraction_bar,
    build_bar_model,
    check_visual_spec_leak
)


def test_ten_frame_builder():
    spec = build_ten_frame(
        frames=[{"filled": 8}, {"filled": 6}],
        highlights=[{"from_frame": 1, "to_frame": 0, "move": 2}],
        mode="current"
    )
    assert spec.type == VisualType.TEN_FRAME
    assert spec.mode == VisualMode.CURRENT
    assert spec.answer_safe is True
    assert len(spec.params["frames"]) == 2
    assert spec.params["frames"][0]["filled"] == 8
    assert spec.params["frames"][1]["filled"] == 6
    assert len(spec.highlights) == 1
    assert spec.highlights[0].move == 2


def test_number_line_builder():
    spec = build_number_line(
        start=14,
        step=-1,
        hops=[{"from": 14, "to": 10, "label": "-4"}],
        mode="current"
    )
    assert spec.type == VisualType.NUMBER_LINE
    assert spec.params["start"] == 14
    assert len(spec.params["hops"]) == 1
    assert spec.params["hops"][0]["to"] == 10


def test_base_ten_blocks_builder():
    spec = build_base_ten_blocks(
        tens=3,
        ones=12,
        regroup=True,
        mode="current"
    )
    assert spec.type == VisualType.BASE_TEN_BLOCKS
    assert spec.params["tens"] == 3
    assert spec.params["ones"] == 12
    assert spec.params["regroup"] is True


def test_array_grid_builder():
    spec = build_array_grid(
        rows=4,
        cols=3,
        color="apple"
    )
    assert spec.type == VisualType.ARRAY_GRID
    assert spec.params["rows"] == 4
    assert spec.params["cols"] == 3
    assert spec.params["color"] == "apple"


def test_fraction_bar_builder():
    spec = build_fraction_bar(
        numerator=2,
        denominator=4,
        target_denominator=8
    )
    assert spec.type == VisualType.FRACTION_BAR
    assert spec.params["numerator"] == 2
    assert spec.params["denominator"] == 4
    assert spec.params["target_denominator"] == 8


def test_bar_model_builder_current_vs_reveal():
    # In current mode, unknown part is None
    spec_current = build_bar_model(
        whole=12,
        parts=[4, 8],
        unknown_index=1,
        mode="current"
    )
    assert spec_current.params["parts"][1] is None
    assert spec_current.answer_safe is True

    # In reveal mode, unknown part is disclosed
    spec_reveal = build_bar_model(
        whole=12,
        parts=[4, 8],
        unknown_index=1,
        mode="reveal"
    )
    assert spec_reveal.params["parts"][1] == 8
    assert spec_reveal.answer_safe is False


def test_visual_leak_checker_catches_target():
    # If a spec in current mode contains the target answer in its params, it must be intercepted
    spec = build_number_line(
        start=10,
        hops=[{"from": 10, "to": 14, "label": "+4"}],
        mode="current"
    )
    is_leak, sanitized, reason = check_visual_spec_leak(
        spec=spec,
        target_answer="14"
    )
    assert is_leak is True
    assert "visual_param_leak_detected" in reason
    assert sanitized.answer_safe is False


def test_visual_leak_checker_permits_reveal():
    spec = build_ten_frame(
        frames=[{"filled": 10}, {"filled": 4}],
        mode="reveal"
    )
    is_leak, _, _ = check_visual_spec_leak(
        spec=spec,
        target_answer="14"
    )
    assert is_leak is False


def test_all_skills_produce_valid_visual_spec():
    from app.services.socratic.skills import skill_registry
    from app.services.visuals.schema import VisualSpec
    from fractions import Fraction

    test_problems = [
        {"op": "+", "a": 8, "b": 6},
        {"op": "-", "a": 14, "b": 6},
        {"op": "+", "a": 15, "b": 27},
        {"op": "-", "a": 42, "b": 17},
        {"op": "*", "a": 4, "b": 3},
        {"type": "fraction_equivalent", "a": Fraction(2, 4)},
        {"type": "word_problem", "total": 15, "part1": 7, "op": "-", "item": "marbles"}
    ]

    for prob in test_problems:
        skill = skill_registry.match(prob)
        assert skill is not None, f"Failed to match skill for {prob}"
        steps = skill.build_steps(prob)
        for s in steps:
            if s.visual_spec:
                validated = VisualSpec.model_validate(s.visual_spec)
                assert validated.type is not None
                assert validated.mode is not None
                assert isinstance(validated.params, dict)
                assert len(validated.alt_text) > 0
