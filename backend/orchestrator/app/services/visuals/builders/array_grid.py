"""
File: orchestrator/app/services/visuals/builders/array_grid.py
Description: Deterministic builder for Array Grid VisualSpec (Multiplication Tables / Equal Groups).
             Implements Architecture v2.1 Section 8.2.4.
"""

from typing import List, Optional
from app.services.visuals.schema import VisualSpec, VisualType, VisualMode


def build_array_grid(
    rows: int,
    cols: int,
    mode: str = "current",
    color: str = "indigo",
    labels: Optional[List[str]] = None,
    alt_text: Optional[str] = None
) -> VisualSpec:
    """
    Builds a deterministic Array Grid VisualSpec for multiplication tables.
    rows: number of groups/rows (1 to 12)
    cols: items per group/columns (1 to 12)
    """
    v_mode = VisualMode(mode) if mode in VisualMode.__members__.values() else VisualMode.CURRENT
    safe_rows = max(1, min(15, int(rows)))
    safe_cols = max(1, min(15, int(cols)))

    default_labels = labels or [f"{safe_rows} rows", f"{safe_cols} items in each row"]
    default_alt = alt_text or f"Array grid showing {safe_rows} rows of {safe_cols} dots."

    return VisualSpec(
        schema_version=1,
        type=VisualType.ARRAY_GRID,
        mode=v_mode,
        answer_safe=(v_mode != VisualMode.REVEAL),
        params={
            "rows": safe_rows,
            "cols": safe_cols,
            "color": color
        },
        highlights=[],
        labels=default_labels,
        alt_text=default_alt
    )
