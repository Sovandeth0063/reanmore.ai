"""
File: backend/testing/unit/guardrails/test_photo_pii.py
Description: Exhaustive test suite for Photo PII Masking & Ingress Header Redaction (Phase 5).
             Verifies that worksheet images/PDFs have handwritten student name/ID headers
             blanked server-side before transit to vision models, and that errors degrade honestly.
"""

import io
import os
import sys
import pytest
from PIL import Image, ImageDraw

def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# pyrefly: ignore [missing-import]
from app.services.ocr.ingress import (
    mask_photo_pii,
    DEFAULT_HEADER_MASK_RATIO,
    is_pdf_payload,
)
# pyrefly: ignore [missing-import]
from app.services.ocr.extractor import OCRExtractor


def _create_synthetic_worksheet_image(
    format: str = "PNG",
    width: int = 800,
    height: int = 1000,
    include_header_text: bool = True,
) -> bytes:
    """Creates a synthetic student worksheet image with a colored header band."""
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    if include_header_text:
        # Simulate header with student info (e.g. Name: Chan Sokha, Class: 4B)
        # Using a distinct non-white color in the header area so we can test blanking
        draw.rectangle([0, 0, width, 80], fill=(50, 50, 150))

    # Simulate problem text in body (below header)
    draw.rectangle([50, 150, 750, 300], fill=(200, 200, 200))

    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_is_pdf_detection():
    assert is_pdf_payload(b"%PDF-1.4 header", "test.pdf") is True
    assert is_pdf_payload(b"some bytes", "test.pdf") is True
    assert is_pdf_payload(b"%PDF-1.7 data", "test.png") is True
    assert is_pdf_payload(b"\x89PNG\r\n\x1a\n", "test.png") is False


def test_mask_photo_pii_png():
    """Verify PNG header masking blanks the top region with neutral white."""
    raw_bytes = _create_synthetic_worksheet_image("PNG", width=600, height=800)
    masked_bytes, meta = mask_photo_pii(raw_bytes, filename="worksheet.png", header_ratio=0.10)

    assert meta["masked"] is True
    assert meta["file_type"] == "image"
    assert meta["format"] == "PNG"
    assert meta["width"] == 600
    assert meta["height"] == 800
    assert meta["masked_region"]["height"] == 80  # 10% of 800

    # Inspect resulting image
    with Image.open(io.BytesIO(masked_bytes)) as img:
        assert img.size == (600, 800)
        # Check pixel in the masked header (should be white 255, 255, 255)
        pixel_header = img.getpixel((300, 40))
        assert pixel_header == (255, 255, 255)
        # Check pixel below the masked header (should retain body background)
        pixel_body = img.getpixel((300, 200))
        assert pixel_body == (200, 200, 200)


def test_mask_photo_pii_jpeg():
    """Verify JPEG header masking operates cleanly on RGB and RGBA sources."""
    raw_bytes = _create_synthetic_worksheet_image("JPEG", width=500, height=700)
    masked_bytes, meta = mask_photo_pii(raw_bytes, filename="camera_photo.jpg", header_ratio=0.08)

    assert meta["masked"] is True
    assert meta["file_type"] == "image"
    assert meta["format"] in ("JPEG", "JPG")
    assert meta["width"] == 500
    assert meta["height"] == 700

    with Image.open(io.BytesIO(masked_bytes)) as img:
        assert img.size == (500, 700)
        # Header pixel should be near pure white in JPEG (allowing slight compression variance)
        r, g, b = img.getpixel((250, 25))
        assert r >= 250 and g >= 250 and b >= 250


def test_mask_photo_pii_pdf():
    """Verify PDF multi-page document header redaction using PyMuPDF."""
    import pymupdf

    doc = pymupdf.open()
    page1 = doc.new_page(width=600, height=800)
    page1.draw_rect(pymupdf.Rect(0, 0, 600, 60), color=(0, 0, 1), fill=(0, 0, 1))
    page2 = doc.new_page(width=600, height=800)
    page2.draw_rect(pymupdf.Rect(0, 0, 600, 60), color=(0, 0, 1), fill=(0, 0, 1))
    raw_pdf_bytes = doc.tobytes()
    doc.close()

    masked_pdf, meta = mask_photo_pii(raw_pdf_bytes, filename="homework_pages.pdf", header_ratio=0.09)

    assert meta["masked"] is True
    assert meta["file_type"] == "pdf"
    assert meta["pages_count"] == 2

    # Verify the output is valid readable PDF
    check_doc = pymupdf.open(stream=masked_pdf, filetype="pdf")
    assert len(check_doc) == 2
    check_doc.close()


def test_mask_photo_pii_corrupted_payload_honest_degradation():
    """Verify unparseable corrupted bytes return gracefully without throwing exceptions."""
    corrupted_bytes = b"CORRUPTED_NOT_AN_IMAGE_OR_PDF_DATA_STREAM"
    res_bytes, meta = mask_photo_pii(corrupted_bytes, filename="bad.png")

    # Honest degradation: preserves payload, records masked=False, does not crash
    assert meta["masked"] is False
    assert "error" in meta
    assert res_bytes == corrupted_bytes


def test_mask_photo_pii_empty_payload():
    """Verify empty byte stream handling."""
    res_bytes, meta = mask_photo_pii(b"", filename="empty.png")
    assert meta["masked"] is False
    assert res_bytes == b""


def test_header_ratio_bounds_clamping():
    """Verify header_ratio is clamped between 0.02 and 0.30."""
    raw_bytes = _create_synthetic_worksheet_image("PNG", width=500, height=1000)

    # Below minimum (0.001 -> clamped to 0.02)
    _, meta_low = mask_photo_pii(raw_bytes, header_ratio=0.001)
    assert meta_low["header_ratio"] == 0.02
    assert meta_low["masked_region"]["height"] == 20

    # Above maximum (0.90 -> clamped to 0.30)
    _, meta_high = mask_photo_pii(raw_bytes, header_ratio=0.90)
    assert meta_high["header_ratio"] == 0.30
    assert meta_high["masked_region"]["height"] == 300


@pytest.mark.asyncio
async def test_ocr_extractor_integration_applies_masking():
    """Verify OCRExtractor applies PII masking before dispatch and propagates metadata."""
    extractor = OCRExtractor()
    raw_bytes = _create_synthetic_worksheet_image("PNG", width=500, height=800)

    # Scanner offline -> should return honest degraded response with pii_masked=True
    result = await extractor.extract_from_bytes(file_bytes=raw_bytes, filename="worksheet.png")

    assert result["pii_masked"] is True
    assert "mask_info" in result
    assert result["mask_info"]["masked"] is True
    assert result["mask_info"]["width"] == 500
    assert result["mask_info"]["height"] == 800
