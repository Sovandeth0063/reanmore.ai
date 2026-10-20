"""
File: orchestrator/app/services/visuals/builders/number_line.py
Description: Deterministic builder for Number Line VisualSpec (Subtraction within 20 / Hop back to 10).
             Implements Architecture v2.1 Section 8.2.2.
"""

from typing import List, Dict, Any, Optional
from app.services.visuals.schema import VisualSpec, VisualType, VisualMode, VisualHighlight


def build_number_line(
    start: int,
    step: int = -1,
    hops: Optional[List[Dict[str, Any]]] = None,
    mode: str = "current",
    labels: Optional[List[str]] = None,
    alt_text: Optional[str] = None
) -> VisualSpec:
    """
    Builds a deterministic Number Line VisualSpec.
    hops: list of hop dicts, e.g. [{"from": 14, "to": 10, "label": "-4"}]
    """
    v_mode = VisualMode(mode) if mode in VisualMode.__members__.values() else VisualMode.CURRENT
    safe_hops = hops or []

    default_labels = labels or [f"Start at {start}"]
    default_alt = alt_text or f"Number line starting at {start} with {len(safe_hops)} hops."

    return VisualSpec(
        schema_version=1,
        type=VisualType.NUMBER_LINE,
        mode=v_mode,
        answer_safe=(v_mode != VisualMode.REVEAL),
        params={
            "start": int(start),
            "step": int(step),
            "hops": safe_hops
        },
        highlights=[],
        labels=default_labels,
        alt_text=default_alt
    )
