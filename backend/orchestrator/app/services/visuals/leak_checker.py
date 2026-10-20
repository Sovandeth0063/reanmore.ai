"""
File: orchestrator/app/services/visuals/leak_checker.py
Description: Multi-point visual leak scanner verifying that SVG VisualSpecs do not
             disclose unsolved step answers or final targets.
             Implements Architecture v2.1 Section 8.3.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from fractions import Fraction

from app.services.visuals.schema import VisualSpec, VisualMode
from app.services.guardrails.leak_guard import safe_eval_ast, _extract_target_value


def _extract_scalar_numbers(obj: Any) -> List[Fraction]:
    """Recursively collects all scalar numeric values from a nested dictionary or list."""
    numbers: List[Fraction] = []
    if isinstance(obj, dict):
        for v in obj.values():
            numbers.extend(_extract_scalar_numbers(v))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            numbers.extend(_extract_scalar_numbers(item))
    elif isinstance(obj, (int, float)):
        numbers.append(Fraction(obj).limit_denominator(1000))
    elif isinstance(obj, str):
        val = safe_eval_ast(obj)
        if val is not None:
            numbers.append(val)
    return numbers


def check_visual_spec_leak(
    spec: VisualSpec,
    target_answer: Optional[str] = None,
    unsolved_targets: Optional[List[str]] = None,
    problem_numbers: Optional[Set[Any]] = None
) -> Tuple[bool, VisualSpec, Optional[str]]:
    """
    Scans a VisualSpec before serialization to frontend:
    1. In REVEAL mode: permitted to display solution.
    2. In CURRENT mode: ensures no param, label, or alt_text equals active target or future unsolved targets.
    3. In EXAMPLE mode: ensures zero collision with the student's problem numbers and targets.

    Returns:
        (is_leak: bool, checked_spec: VisualSpec, reason: Optional[str])
    """
    if spec.mode == VisualMode.REVEAL:
        return False, spec, None

    # Target values to forbid in CURRENT mode
    forbidden_targets: Set[Fraction] = set()
    if target_answer:
        t_val = _extract_target_value(target_answer)
        if t_val is not None:
            forbidden_targets.add(t_val)
    for u in (unsolved_targets or []):
        u_val = _extract_target_value(u)
        if u_val is not None:
            forbidden_targets.add(u_val)

    # 1. Check params scalars
    param_numbers = _extract_scalar_numbers(spec.params)
    for num in param_numbers:
        if spec.mode == VisualMode.CURRENT and num in forbidden_targets:
            # Leak detected in current mode parameters!
            sanitized = spec.model_copy(deep=True)
            sanitized.answer_safe = False
            sanitized.labels = ["Visual scaffolding hidden for current step"]
            sanitized.alt_text = "Visual model scaffolding."
            return True, sanitized, f"visual_param_leak_detected ({num})"

        if spec.mode == VisualMode.EXAMPLE and problem_numbers:
            # Verify disjointness with problem numbers
            prob_fracs = set()
            for p in problem_numbers:
                p_v = _extract_target_value(str(p))
                if p_v is not None:
                    prob_fracs.add(p_v)
            if num in prob_fracs:
                return True, spec, f"example_visual_collision_detected ({num})"

    # 2. Check labels and alt_text for target leaks
    text_to_scan = " ".join(spec.labels) + " " + spec.alt_text
    for target in forbidden_targets:
        # Check integer/float token representation
        target_str = str(int(target)) if target.denominator == 1 else str(float(target))
        if f" {target_str} " in f" {text_to_scan} " or f": {target_str}" in text_to_scan or f"={target_str}" in text_to_scan:
            sanitized = spec.model_copy(deep=True)
            sanitized.answer_safe = False
            sanitized.labels = ["Visual model"]
            sanitized.alt_text = "Visual model scaffolding."
            return True, sanitized, f"visual_label_leak_detected ({target_str})"

    return False, spec, None
