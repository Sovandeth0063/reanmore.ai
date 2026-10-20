"""
File: orchestrator/app/services/visuals/builders/fraction_bar.py
Description: Deterministic builder for Fraction Bar VisualSpec (Equivalent Fractions).
             Implements Architecture v2.1 Section 8.2.5.
"""

from typing import List, Optional
from app.services.visuals.schema import VisualSpec, VisualType, VisualMode


def build_fraction_bar(
    numerator: int,
    denominator: int,
    target_denominator: Optional[int] = None,
    mode: str = "current",
    labels: Optional[List[str]] = None,
    alt_text: Optional[str] = None
) -> VisualSpec:
    """
    Builds a deterministic Fraction Bar VisualSpec.
    numerator: shaded parts (0 to denominator)
    denominator: total parts (1 to 24)
    target_denominator: optional comparison fraction bar denominator
    """
    v_mode = VisualMode(mode) if mode in VisualMode.__members__.values() else VisualMode.CURRENT
    safe_den = max(1, min(30, int(denominator)))
    safe_num = max(0, min(safe_den, int(numerator)))

    params = {
        "numerator": safe_num,
        "denominator": safe_den
    }
    if target_denominator:
        params["target_denominator"] = max(1, min(30, int(target_denominator)))

    default_labels = labels or [f"{safe_num}/{safe_den}"]
    default_alt = alt_text or f"Fraction bar divided into {safe_den} parts with {safe_num} shaded."

    return VisualSpec(
        schema_version=1,
        type=VisualType.FRACTION_BAR,
        mode=v_mode,
        answer_safe=(v_mode != VisualMode.REVEAL),
        params=params,
        highlights=[],
        labels=default_labels,
        alt_text=default_alt
    )
