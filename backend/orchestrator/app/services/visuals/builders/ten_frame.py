"""
File: orchestrator/app/services/visuals/builders/ten_frame.py
Description: Deterministic builder for Ten-Frame VisualSpec (Addition within 20 / Make-a-Ten).
             Implements Architecture v2.1 Section 8.2.1.
"""

from typing import List, Dict, Any, Optional
from app.services.visuals.schema import VisualSpec, VisualType, VisualMode, VisualHighlight


def build_ten_frame(
    frames: List[Dict[str, int]],
    highlights: Optional[List[Dict[str, Any]]] = None,
    mode: str = "current",
    labels: Optional[List[str]] = None,
    alt_text: Optional[str] = None,
    color: str = "apple"
) -> VisualSpec:
    """
    Builds a deterministic Ten-Frame VisualSpec.
    frames: list of frame dicts with "filled" count (0 to 10), e.g. [{"filled": 8}, {"filled": 6}]
    """
    safe_frames = []
    for f in frames:
        filled = max(0, min(10, int(f.get("filled", 0))))
        safe_frames.append({"filled": filled})

    converted_highlights = []
    if highlights:
        for h in highlights:
            converted_highlights.append(VisualHighlight(**h))

    v_mode = VisualMode(mode) if mode in VisualMode.__members__.values() else VisualMode.CURRENT

    default_labels = labels or [f"Frame {idx + 1}: {f['filled']} counters" for idx, f in enumerate(safe_frames)]
    default_alt = alt_text or f"Ten-frames displaying {', '.join(str(f['filled']) for f in safe_frames)} counters."

    return VisualSpec(
        schema_version=1,
        type=VisualType.TEN_FRAME,
        mode=v_mode,
        answer_safe=(v_mode != VisualMode.REVEAL),
        params={
            "frames": safe_frames,
            "color": color
        },
        highlights=converted_highlights,
        labels=default_labels,
        alt_text=default_alt
    )
