"""
File: orchestrator/app/services/visuals/builders/base_ten_blocks.py
Description: Deterministic builder for Base-Ten Blocks VisualSpec (2-Digit Regrouping / Borrowing).
             Implements Architecture v2.1 Section 8.2.3.
"""

from typing import List, Dict, Any, Optional
from app.services.visuals.schema import VisualSpec, VisualType, VisualMode, VisualHighlight


def build_base_ten_blocks(
    tens: int,
    ones: int,
    hundreds: int = 0,
    regroup: bool = False,
    highlights: Optional[List[Dict[str, Any]]] = None,
    mode: str = "current",
    labels: Optional[List[str]] = None,
    alt_text: Optional[str] = None
) -> VisualSpec:
    """
    Builds a deterministic Base-Ten Blocks VisualSpec.
    tens: count of 10-rods (0 to 20)
    ones: count of unit blocks (0 to 30)
    regroup: whether regrouping/borrowing is active in this step
    """
    v_mode = VisualMode(mode) if mode in VisualMode.__members__.values() else VisualMode.CURRENT

    converted_highlights = []
    if highlights:
        for h in highlights:
            converted_highlights.append(VisualHighlight(**h))

    default_labels = labels or [f"{tens} tens rods", f"{ones} ones blocks"]
    default_alt = alt_text or f"Base-ten blocks showing {tens} tens rods and {ones} unit cubes."

    return VisualSpec(
        schema_version=1,
        type=VisualType.BASE_TEN_BLOCKS,
        mode=v_mode,
        answer_safe=(v_mode != VisualMode.REVEAL),
        params={
            "hundreds": int(hundreds),
            "tens": int(tens),
            "ones": int(ones),
            "regroup": bool(regroup)
        },
        highlights=converted_highlights,
        labels=default_labels,
        alt_text=default_alt
    )
