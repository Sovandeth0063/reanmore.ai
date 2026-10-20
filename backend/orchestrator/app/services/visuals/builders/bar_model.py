"""
File: orchestrator/app/services/visuals/builders/bar_model.py
Description: Deterministic builder for Singapore Part-Whole Bar Model VisualSpec (Word Problems).
             Implements Architecture v2.1 Section 8.2.6.
"""

from typing import List, Optional, Any
from app.services.visuals.schema import VisualSpec, VisualType, VisualMode


def build_bar_model(
    whole: Optional[int],
    parts: List[Optional[int]],
    unknown_index: Optional[int] = None,
    mode: str = "current",
    item_label: str = "items",
    labels: Optional[List[str]] = None,
    alt_text: Optional[str] = None
) -> VisualSpec:
    """
    Builds a deterministic Singapore-style Part-Whole Bar Model VisualSpec.
    whole: total quantity across all parts (or None if unknown)
    parts: list of individual part quantities (None indicates the unknown part)
    unknown_index: 0-indexed position of unknown part (if unknown)
    """
    v_mode = VisualMode(mode) if mode in VisualMode.__members__.values() else VisualMode.CURRENT

    safe_parts = []
    for idx, p in enumerate(parts):
        if p is None or idx == unknown_index:
            safe_parts.append(None if v_mode != VisualMode.REVEAL else p)
        else:
            safe_parts.append(int(p))

    default_labels = labels or []
    if not default_labels:
        if whole is not None:
            default_labels.append(f"Total: {whole} {item_label}")
        for idx, p in enumerate(safe_parts):
            if p is not None:
                default_labels.append(f"Part {idx + 1}: {p}")
            else:
                default_labels.append(f"Part {idx + 1}: ?")

    default_alt = alt_text or f"Part-whole bar model with total {whole or 'unknown'} and {len(safe_parts)} segments."

    return VisualSpec(
        schema_version=1,
        type=VisualType.BAR_MODEL,
        mode=v_mode,
        answer_safe=(v_mode != VisualMode.REVEAL),
        params={
            "whole": int(whole) if whole is not None else None,
            "parts": safe_parts,
            "unknown_index": unknown_index,
            "item_label": item_label
        },
        highlights=[],
        labels=default_labels,
        alt_text=default_alt
    )
