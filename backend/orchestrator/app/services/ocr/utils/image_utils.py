"""
Shared image utility helpers used across the pipeline.
"""
from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
BBox = list[float]  # [x1, y1, x2, y2] absolute pixel coords


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def bgr_to_pil(img: np.ndarray) -> Image.Image:
    """Convert BGR NumPy array to PIL RGB Image."""
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def pil_to_bgr(img: Image.Image) -> np.ndarray:
    """Convert PIL RGB Image to BGR NumPy array."""
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def ndarray_to_base64(img: np.ndarray, fmt: str = "PNG") -> str:
    """Encode a BGR NumPy image to a base64 string (PNG by default)."""
    pil = bgr_to_pil(img)
    buf = io.BytesIO()
    pil.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def base64_to_ndarray(b64: str) -> np.ndarray:
    """Decode a base64 string back to a BGR NumPy image."""
    data = base64.b64decode(b64)
    pil = Image.open(io.BytesIO(data)).convert("RGB")
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def load_image(path: str | Path) -> np.ndarray:
    """Load an image file as a BGR NumPy array."""
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img


def save_image(img: np.ndarray, path: str | Path) -> None:
    """Save a BGR NumPy array to disk."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img)


# ---------------------------------------------------------------------------
# Region helpers
# ---------------------------------------------------------------------------

def crop_region(img: np.ndarray, bbox: BBox, padding: int = 4) -> np.ndarray:
    """
    Crop a rectangular region from an image.

    Args:
        img:     BGR image.
        bbox:    [x1, y1, x2, y2] in absolute pixel coordinates.
        padding: Extra pixels to include around the bbox (clamped to image bounds).

    Returns:
        Cropped BGR image.
    """
    h, w = img.shape[:2]
    x1 = max(0, int(bbox[0]) - padding)
    y1 = max(0, int(bbox[1]) - padding)
    x2 = min(w, int(bbox[2]) + padding)
    y2 = min(h, int(bbox[3]) + padding)
    return img[y1:y2, x1:x2].copy()


def bbox_area(bbox: BBox) -> float:
    """Return the pixel area of a [x1, y1, x2, y2] bounding box."""
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def resize_to_max_side(img: np.ndarray, max_side: int) -> np.ndarray:
    """
    Proportionally resize so the longer dimension equals max_side.
    Does nothing if the image is already small enough.
    """
    h, w = img.shape[:2]
    if max(h, w) <= max_side:
        return img
    scale = max_side / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def get_image_dimensions(img: np.ndarray) -> tuple[int, int]:
    """Return (width, height) of a NumPy image."""
    h, w = img.shape[:2]
    return w, h


# ---------------------------------------------------------------------------
# Reading-order helper
# ---------------------------------------------------------------------------

def sort_regions_reading_order(
    regions: list[dict],
    n_columns: int = 1,
    column_gap_ratio: float = 0.45,
) -> list[dict]:
    """
    Sort layout regions into reading order (top-to-bottom, left-to-right).

    For 2-column layouts, regions are assigned to a column first by their
    horizontal centre, then sorted top-to-bottom within each column.

    Args:
        regions:          List of region dicts, each with a 'bbox' key.
        n_columns:        Expected number of columns (1 or 2).
        column_gap_ratio: Fraction of page width used to divide columns.

    Returns:
        Re-ordered list of regions.
    """
    if not regions:
        return regions

    if n_columns == 1:
        return sorted(regions, key=lambda r: (r["bbox"][1], r["bbox"][0]))

    # 2-column: split by horizontal centre
    all_cx = [(r["bbox"][0] + r["bbox"][2]) / 2 for r in regions]
    page_width = max(r["bbox"][2] for r in regions)
    split_x = page_width * column_gap_ratio

    left_col = [r for r, cx in zip(regions, all_cx) if cx <= split_x]
    right_col = [r for r, cx in zip(regions, all_cx) if cx > split_x]

    left_col.sort(key=lambda r: r["bbox"][1])
    right_col.sort(key=lambda r: r["bbox"][1])

    return left_col + right_col
