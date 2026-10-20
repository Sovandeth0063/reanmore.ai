"""
File: orchestrator/app/services/ocr/ingress.py
Description: Ingress Photo PII Sanitizer & Header Redactor (Spec Section 9, Phase 5).
             - Inspects incoming worksheet images/PDFs before cloud vision transit.
             - Redacts the top header region (top 8-10%) containing student names,
               class IDs, dates, and school markings.
             - Blanks the region with neutral paper white background before sending
               to OCR / Gemini Vision.
             - Gracefully degrades without failing if image bytes are corrupted.
"""

import io
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("orchestrator.ocr.ingress")

# Default header proportion to redact (elementary worksheet top 9% header block)
DEFAULT_HEADER_MASK_RATIO: float = 0.09
NEUTRAL_WHITE_RGB: Tuple[int, int, int] = (255, 255, 255)


def is_pdf_payload(file_bytes: bytes, filename: str) -> bool:
    """Detects whether payload is a PDF by magic bytes or file extension."""
    if filename and filename.lower().endswith(".pdf"):
        return True
    return file_bytes.startswith(b"%PDF")


def mask_photo_pii(
    file_bytes: bytes,
    filename: str = "worksheet.png",
    header_ratio: float = DEFAULT_HEADER_MASK_RATIO,
    fill_color: Tuple[int, int, int] = NEUTRAL_WHITE_RGB,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Masks the top header region of an image or PDF to redact handwritten
    student names, IDs, and personal identifiers before downstream vision processing.

    Returns:
        (sanitized_bytes, metadata_dict)
    """
    if not file_bytes:
        return file_bytes, {
            "masked": False,
            "error": "Empty file payload",
            "filename": filename,
        }

    # Ensure ratio is within sane bounds (between 2% and 30%)
    clamped_ratio = max(0.02, min(header_ratio, 0.30))

    # ── PDF Document Path ────────────────────────────────────────────────────
    if is_pdf_payload(file_bytes, filename):
        try:
            import pymupdf  # PyMuPDF

            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            pages_count = len(doc)
            for page in doc:
                w = page.rect.width
                h = page.rect.height
                mask_h = h * clamped_ratio
                rect = pymupdf.Rect(0, 0, w, mask_h)
                # Draw white opaque redaction rectangle over header
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            masked_bytes = doc.tobytes()
            doc.close()

            logger.info(
                f"[PhotoPII] Successfully masked header on PDF '{filename}' "
                f"({pages_count} pages, ratio={clamped_ratio:.2f})."
            )
            return masked_bytes, {
                "masked": True,
                "file_type": "pdf",
                "filename": filename,
                "pages_count": pages_count,
                "header_ratio": clamped_ratio,
                "reason": "Redacted student header PII before vision processing",
            }
        except Exception as e:
            logger.warning(
                f"[PhotoPII] PDF header masking failed ({e}). Returning original payload honestly."
            )
            return file_bytes, {
                "masked": False,
                "file_type": "pdf",
                "filename": filename,
                "error": str(e),
            }

    # ── Image (PNG, JPEG, WEBP, etc.) Path ───────────────────────────────────
    try:
        from PIL import Image, ImageDraw

        with Image.open(io.BytesIO(file_bytes)) as img:
            fmt = img.format or "PNG"
            mode = img.mode

            # If mode doesn't support RGB drawing directly (e.g. palette 'P' or '1')
            if mode in ("P", "1"):
                work_img = img.convert("RGB")
                save_mode = "RGB"
            else:
                work_img = img.copy()
                save_mode = mode

            w, h = work_img.size
            mask_h = max(1, int(h * clamped_ratio))

            draw = ImageDraw.Draw(work_img)
            # Mask the top banner region containing name, class, date
            draw.rectangle([0, 0, w, mask_h], fill=fill_color)

            # Write out to bytes using the detected or fallback format
            buf = io.BytesIO()
            # JPEG doesn't support RGBA
            if fmt.upper() in ("JPEG", "JPG") and save_mode == "RGBA":
                work_img = work_img.convert("RGB")

            work_img.save(buf, format=fmt)
            masked_bytes = buf.getvalue()

            logger.info(
                f"[PhotoPII] Successfully masked header on image '{filename}' "
                f"({w}x{h}, masked top {mask_h}px, format={fmt})."
            )
            return masked_bytes, {
                "masked": True,
                "file_type": "image",
                "format": fmt,
                "filename": filename,
                "width": w,
                "height": h,
                "masked_region": {"x": 0, "y": 0, "width": w, "height": mask_h},
                "header_ratio": clamped_ratio,
                "reason": "Redacted student header PII before vision processing",
            }

    except Exception as e:
        logger.warning(
            f"[PhotoPII] Image header masking failed ({e}). Returning original payload honestly."
        )
        return file_bytes, {
            "masked": False,
            "file_type": "image",
            "filename": filename,
            "error": str(e),
        }
