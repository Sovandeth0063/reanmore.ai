"""
Bounding-box utilities for the homework OCR pipeline.

  validate_answer_area_bbox(bbox, label) -> list[str]
      Returns human-readable problems. Empty list = valid.

  convert_bboxes_to_pixels(page, img_w, img_h) -> None
      Mutates every AnswerAreaEntry.bbox from 0-1000 scale to pixels.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_NORM_MAX = 1000  # prompt instructs coordinates 0-1000


def validate_answer_area_bbox(
    bbox: Optional[list],
    label: str = "",
) -> list[str]:
    """
    Rules:
    - Exactly 4 elements
    - All must be integers
    - 0 <= each <= 1000
    - x1 < x2 and y1 < y2
    Returns empty list if valid.
    """
    if bbox is None:
        return []

    tag = f"[{label}] " if label else ""

    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return [f"{tag}bbox must have 4 elements, got {bbox!r}"]

    values: list[Optional[int]] = []
    problems: list[str] = []
    for i, v in enumerate(bbox):
        try:
            iv = int(v)
            if float(v) != iv:
                problems.append(f"{tag}bbox[{i}]={v!r} is not an integer")
            values.append(iv)
        except (ValueError, TypeError):
            problems.append(f"{tag}bbox[{i}]={v!r} is not a number")
            values.append(None)

    if any(v is None for v in values):
        return problems

    x1, y1, x2, y2 = values  # type: ignore[misc]

    for name, val in [("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)]:
        if not (0 <= val <= _NORM_MAX):
            problems.append(f"{tag}{name}={val} out of [0,{_NORM_MAX}]")

    if x1 >= x2:
        problems.append(f"{tag}x1={x1} >= x2={x2} (must be x1 < x2)")
    if y1 >= y2:
        problems.append(f"{tag}y1={y1} >= y2={y2} (must be y1 < y2)")

    return problems


def convert_bboxes_to_pixels(page, img_w: int, img_h: int) -> None:
    """
    Convert every answer_area.bbox on *page* from the prompt's 0-1000 scale
    to pixel coordinates. Mutates in-place.

        px_x = round(norm_x * img_w / 1000)
        px_y = round(norm_y * img_h / 1000)
    """
    if img_w <= 0 or img_h <= 0:
        logger.warning(
            "convert_bboxes_to_pixels: invalid image size %dx%d — skipping", img_w, img_h
        )
        return

    sx = img_w / _NORM_MAX
    sy = img_h / _NORM_MAX
    count = 0

    for section in page.sections:
        for question in section.questions:
            for area in question.answer_areas:
                if area.bbox is not None and len(area.bbox) == 4:
                    x1, y1, x2, y2 = area.bbox
                    area.bbox = [
                        round(x1 * sx),
                        round(y1 * sy),
                        round(x2 * sx),
                        round(y2 * sy),
                    ]
                    count += 1
            for elem in question.elements:
                if hasattr(elem, "bbox") and elem.bbox is not None and len(elem.bbox) == 4:
                    ex1, ey1, ex2, ey2 = elem.bbox
                    elem.bbox = [
                        round(ex1 * sx),
                        round(ey1 * sy),
                        round(ex2 * sx),
                        round(ey2 * sy),
                    ]
                    count += 1

    logger.debug(
        "Converted %d bbox(es) to pixels (%dx%d)", count, img_w, img_h
    )
