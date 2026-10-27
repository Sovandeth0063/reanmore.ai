"""
PDF → list-of-images conversion using PyMuPDF (fitz).
Each page is rendered at a resolution appropriate for OCR/VLM.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# DPI for rendering PDF pages.  300 DPI is high enough for OCR without
# producing enormous images.  The preprocessing step will resize further.
RENDER_DPI = 300
RENDER_MATRIX = fitz.Matrix(RENDER_DPI / 72, RENDER_DPI / 72)


def pdf_to_images(pdf_path: str | Path) -> list[np.ndarray]:
    """
    Convert every page of a PDF to a NumPy BGR image array.

    Returns:
        List of images, one per page, in BGR colour order (OpenCV convention).
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    images: list[np.ndarray] = []
    doc = fitz.open(str(pdf_path))

    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=RENDER_MATRIX, alpha=False)

            # Convert pixmap → PIL Image → NumPy BGR
            img_pil = Image.open(io.BytesIO(pix.tobytes("png")))
            img_rgb = np.array(img_pil.convert("RGB"))
            img_bgr = img_rgb[:, :, ::-1].copy()   # RGB → BGR

            images.append(img_bgr)
            logger.debug("Rendered PDF page %d  (%dx%d)", page_index + 1, img_bgr.shape[1], img_bgr.shape[0])
    finally:
        doc.close()

    logger.info("Converted %d PDF pages from '%s'", len(images), pdf_path.name)
    return images


def page_count(pdf_path: str | Path) -> int:
    """Return the number of pages in a PDF without rendering them."""
    doc = fitz.open(str(pdf_path))
    n = len(doc)
    doc.close()
    return n
