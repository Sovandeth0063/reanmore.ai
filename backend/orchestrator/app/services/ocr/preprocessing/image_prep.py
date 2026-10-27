"""
Image preprocessing pipeline for phone photos of homework.

Steps applied (in order):
  1. Detect page boundary (contour / document edge detection)
  2. Perspective correction (four-point transform)
  3. Deskew (Hough-line skew estimation)
  4. Shadow / background normalisation
  5. Contrast enhancement (CLAHE)
  6. Denoising (fastNlMeansDenoisingColored)
  7. Resize to max long-side

The module always returns BOTH the original and processed images so the VLM
can refer to the original if needed.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

from app.services.ocr.utils.image_utils import resize_to_max_side

logger = logging.getLogger(__name__)


@dataclass
class PreprocessedImage:
    original_image: np.ndarray   # Unchanged input (BGR)
    processed_image: np.ndarray  # After all preprocessing steps (BGR)
    was_perspective_corrected: bool = False
    was_deskewed: bool = False
    skew_angle_degrees: float = 0.0
    width: int = 0
    height: int = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order four corner points as: top-left, top-right, bottom-right, bottom-left.
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left  (smallest sum)
    rect[2] = pts[np.argmax(s)]   # bot-right (largest sum)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right (smallest diff)
    rect[3] = pts[np.argmax(diff)]  # bot-left  (largest diff)
    return rect


def _four_point_transform(img: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Apply a perspective transform given four corner points."""
    rect = _order_points(pts)
    tl, tr, br, bl = rect

    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_w = int(max(width_a, width_b))

    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_h = int(max(height_a, height_b))

    dst = np.array(
        [[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, M, (max_w, max_h))


def _detect_page_contour(img: np.ndarray) -> np.ndarray | None:
    """
    Try to find a rectangular document boundary in the image.
    Only returns a page contour if it covers the vast majority of the photo (>65%)
    and spans near the image boundaries, avoiding false positives on inner tables/boxes.
    """
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur + edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 75, 200)

    # Dilate to close small gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours[:5]:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        if len(approx) == 4:
            area = cv2.contourArea(approx)
            # Must cover at least 65% of the total image area
            if area > 0.65 * h * w:
                pts = approx.reshape(4, 2)
                xs = pts[:, 0]
                ys = pts[:, 1]
                # Corners must span near image boundaries
                if (xs.min() < 0.20 * w and xs.max() > 0.80 * w and
                    ys.min() < 0.20 * h and ys.max() > 0.80 * h):
                    return pts.astype("float32")

    return None


def _estimate_skew(img: np.ndarray) -> float:
    """
    Estimate the skew angle of a document image using Hough lines.

    Returns angle in degrees (positive = counter-clockwise tilt).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    lines = cv2.HoughLinesP(
        binary, 1, np.pi / 180,
        threshold=100, minLineLength=100, maxLineGap=10
    )

    if lines is None:
        return 0.0

    angles = []
    for line in lines:
        pts = line.reshape(-1)
        if len(pts) < 4:
            continue
        x1, y1, x2, y2 = pts[:4]
        if x2 != x1:
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Only consider near-horizontal lines (within ±45°)
            if abs(angle) < 45:
                angles.append(angle)

    if not angles:
        return 0.0

    median_angle = float(np.median(angles))
    return median_angle


def _deskew(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by -angle to correct skew."""
    if abs(angle) < 0.3:   # ignore tiny angles
        return img
    h, w = img.shape[:2]
    cx, cy = w / 2, h / 2
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    rotated = cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def _remove_shadows(img: np.ndarray) -> np.ndarray:
    """
    Normalise uneven illumination / shadows.
    Scales kernel proportionally with image size.
    """
    h, w = img.shape[:2]
    ksize = max(3, int(min(w, h) * 0.015))
    if ksize % 2 == 0:
        ksize += 1

    result_channels = []
    for ch in cv2.split(img):
        bg = cv2.dilate(ch, np.ones((ksize, ksize), np.uint8), iterations=5)
        blur_k = max(5, int(min(w, h) * 0.04))
        if blur_k % 2 == 0:
            blur_k += 1
        bg = cv2.GaussianBlur(bg, (blur_k, blur_k), 0)
        norm = cv2.divide(ch.astype(np.float32), bg.astype(np.float32) + 1e-5)
        norm = np.clip(norm * 255, 0, 255).astype(np.uint8)
        result_channels.append(norm)
    return cv2.merge(result_channels)


def _enhance_contrast(img: np.ndarray) -> np.ndarray:
    """Apply CLAHE (Adaptive Histogram Equalisation) to the L channel in LAB."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    lab = cv2.merge([l_ch, a_ch, b_ch])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _denoise(img: np.ndarray) -> np.ndarray:
    """Fast colour denoising."""
    return cv2.fastNlMeansDenoisingColored(img, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess_image(
    img: np.ndarray,
    max_long_side: int = 2000,
    attempt_perspective: bool = True,
    attempt_deskew: bool = True,
    remove_shadows: bool = True,
    enhance_contrast: bool = True,
    denoise: bool = True,
) -> PreprocessedImage:
    """
    Run the full preprocessing pipeline on a single BGR image.

    Always keeps the original untouched.

    Args:
        img:                  Input BGR image.
        max_long_side:        Resize the processed image so its long side ≤ this.
        attempt_perspective:  Try to detect and correct perspective distortion.
        attempt_deskew:       Try to correct small rotational skew.
        remove_shadows:       Apply shadow/illumination normalisation.
        enhance_contrast:     Apply CLAHE contrast enhancement.
        denoise:              Apply noise reduction.

    Returns:
        PreprocessedImage with both original and processed BGR arrays.
    """
    original = img.copy()
    processed = img.copy()
    was_perspective = False
    was_deskewed = False
    skew_angle = 0.0

    # --- Step 1: Perspective correction ---
    if attempt_perspective:
        corners = _detect_page_contour(processed)
        if corners is not None:
            logger.debug("Page contour detected — applying perspective correction")
            processed = _four_point_transform(processed, corners)
            was_perspective = True
        else:
            logger.debug("No clear page contour found — skipping perspective correction")

    # --- Step 2: Deskew ---
    if attempt_deskew:
        skew_angle = _estimate_skew(processed)
        if abs(skew_angle) > 0.3:
            logger.debug("Deskewing by %.2f degrees", skew_angle)
            processed = _deskew(processed, skew_angle)
            was_deskewed = True

    # --- Step 3: Shadow removal ---
    if remove_shadows:
        processed = _remove_shadows(processed)

    # --- Step 4: Contrast enhancement ---
    if enhance_contrast:
        processed = _enhance_contrast(processed)

    # --- Step 5: Denoise ---
    if denoise:
        processed = _denoise(processed)

    # --- Step 6: Resize ---
    processed = resize_to_max_side(processed, max_long_side)

    h, w = processed.shape[:2]
    logger.info(
        "Preprocessing complete: perspective=%s deskew=%s(%.1f°) size=%dx%d",
        was_perspective, was_deskewed, skew_angle, w, h,
    )

    return PreprocessedImage(
        original_image=original,
        processed_image=processed,
        was_perspective_corrected=was_perspective,
        was_deskewed=was_deskewed,
        skew_angle_degrees=skew_angle,
        width=w,
        height=h,
    )
