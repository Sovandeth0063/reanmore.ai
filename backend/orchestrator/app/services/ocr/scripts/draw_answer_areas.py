#!/usr/bin/env python
"""
scripts/draw_answer_areas.py  —  Item 8

Draw every answer_area bounding box and its question_id label on the
original image and save to sample_outputs/annotated_<filename>.png.

Usage:
    python scripts/draw_answer_areas.py <response.json> <image_file>

The response JSON must be a HomeworkResponse produced by this pipeline
(bbox_unit == "px", coordinates already in pixels).

If bbox_unit is "normalized_1000", the script will convert automatically
using the image dimensions.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ── colour palette, one per section label ──────────────────────────────────
_PALETTE = [
    (52, 152, 219),   # blue
    (46, 204, 113),   # green
    (231, 76,  60),   # red
    (155, 89, 182),   # purple
    (230, 126, 34),   # orange
    (26, 188, 156),   # teal
    (241, 196, 15),   # yellow
    (189, 195, 199),  # grey
]


def _colour_for(label: str) -> tuple[int, int, int]:
    idx = sum(ord(c) for c in label) % len(_PALETTE)
    return _PALETTE[idx]


def draw(response_path: str, image_path: str) -> str:
    try:
        import cv2
        import numpy as np
    except ImportError:
        sys.exit("ERROR: OpenCV not found. Install it with: pip install opencv-python")

    # ── load response ───────────────────────────────────────────────────────
    with open(response_path, encoding="utf-8") as f:
        resp = json.load(f)

    bbox_unit = resp.get("bbox_unit", "normalized_1000")

    # ── load image ──────────────────────────────────────────────────────────
    img = cv2.imread(image_path)
    if img is None:
        sys.exit(f"ERROR: cannot load image '{image_path}'")

    img_h, img_w = img.shape[:2]

    # ── draw ────────────────────────────────────────────────────────────────
    total_boxes = 0
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 2

    for page in resp.get("pages", []):
        for section in page.get("sections", []):
            sec_label = section.get("label", "?")
            colour = _colour_for(sec_label)

            for question in section.get("questions", []):
                qid = question.get("id") or question.get("question_no") or "?"

                for area in question.get("answer_areas", []):
                    bbox = area.get("bbox")
                    if not bbox or len(bbox) != 4:
                        continue

                    x1, y1, x2, y2 = bbox

                    # Convert from 0-1000 scale if needed
                    if bbox_unit != "px":
                        x1 = round(x1 * img_w / 1000)
                        y1 = round(y1 * img_h / 1000)
                        x2 = round(x2 * img_w / 1000)
                        y2 = round(y2 * img_h / 1000)

                    # Clamp to image bounds
                    x1 = max(0, min(x1, img_w - 1))
                    y1 = max(0, min(y1, img_h - 1))
                    x2 = max(0, min(x2, img_w - 1))
                    y2 = max(0, min(y2, img_h - 1))

                    if x1 >= x2 or y1 >= y2:
                        continue

                    # Draw semi-transparent fill
                    overlay = img.copy()
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), colour, -1)
                    cv2.addWeighted(overlay, 0.20, img, 0.80, 0, img)

                    # Draw border
                    cv2.rectangle(img, (x1, y1), (x2, y2), colour, thickness)

                    # Draw label
                    kind = area.get("kind", "")
                    label_text = f"{qid}" + (f" ({kind})" if kind else "")
                    label_y = y1 - 6 if y1 > 20 else y2 + 18
                    cv2.putText(
                        img, label_text,
                        (x1, label_y),
                        font, font_scale, colour, thickness,
                        cv2.LINE_AA,
                    )
                    total_boxes += 1

    # ── save ────────────────────────────────────────────────────────────────
    out_dir = Path("sample_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(image_path).stem
    out_path = str(out_dir / f"annotated_{stem}.png")
    cv2.imwrite(out_path, img)

    print(f"Drew {total_boxes} answer_area box(es).")
    print(f"Saved → {os.path.abspath(out_path)}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Draw answer_area bboxes from a HomeworkResponse JSON onto the source image."
    )
    parser.add_argument("response_json", help="Path to the HomeworkResponse JSON file")
    parser.add_argument("image_file", help="Path to the original homework image")
    args = parser.parse_args()

    if not os.path.isfile(args.response_json):
        sys.exit(f"ERROR: '{args.response_json}' not found")
    if not os.path.isfile(args.image_file):
        sys.exit(f"ERROR: '{args.image_file}' not found")

    draw(args.response_json, args.image_file)


if __name__ == "__main__":
    main()
