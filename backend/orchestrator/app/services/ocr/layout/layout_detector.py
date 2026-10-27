"""
Layout / document-understanding module — updated for PaddleOCR 3.x.

PaddleOCR 3.x removed PPStructure and replaced it with:
  - paddleocr.LayoutDetection  → detect region bboxes and labels
  - paddleocr.PaddleOCR        → run OCR on each region

We use LayoutDetection for region detection and PaddleOCR for text extraction.
The VLM handles deeper structural understanding.
"""
from __future__ import annotations

import logging
import re

import numpy as np

from app.services.ocr.schemas.homework import LayoutRegion, RegionType, ReviewFlag, ReviewReason
from app.services.ocr.utils.image_utils import sort_regions_reading_order

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PaddleOCR 3.x LayoutDetection label → our RegionType mapping
# Labels from PP-LayoutParser / PaddleX layout models
# ---------------------------------------------------------------------------
_LABEL_MAP: dict[str, RegionType] = {
    # Common PaddleOCR 3.x layout labels
    "title":            RegionType.HEADER,
    "paragraph_title":  RegionType.HEADER,
    "table_title":      RegionType.HEADER,
    "figure_title":     RegionType.HEADER,
    "text":             RegionType.TEXT_BLOCK,
    "figure":           RegionType.FIGURE,
    "figure_caption":   RegionType.TEXT_BLOCK,
    "table":            RegionType.TABLE,
    "table_caption":    RegionType.TEXT_BLOCK,
    "reference":        RegionType.TEXT_BLOCK,
    "equation":         RegionType.FIGURE,   # send math regions to VLM as figure
    "header":           RegionType.HEADER,
    "page_header":      RegionType.HEADER,
    "footer":           RegionType.TEXT_BLOCK,
    "page_footer":      RegionType.TEXT_BLOCK,
    "list":             RegionType.TEXT_BLOCK,
    "paragraph":        RegionType.TEXT_BLOCK,
    "section":          RegionType.SECTION,
    "abstract":         RegionType.TEXT_BLOCK,
    # PaddleX / DocLayout-YOLO labels (newer models)
    "doc_title":        RegionType.HEADER,
    "heading1":         RegionType.HEADER,
    "heading2":         RegionType.SECTION,
    "heading3":         RegionType.SECTION,
    "image":            RegionType.FIGURE,
    "chart":            RegionType.GRAPH,
    "diagram":          RegionType.DIAGRAM,
    "formula":          RegionType.FIGURE,
    "code":             RegionType.TEXT_BLOCK,
    "checkbox":         RegionType.CHECKBOX,
    "seal":             RegionType.TEXT_BLOCK,
    "unknown":          RegionType.UNKNOWN,
}

# Patterns for reclassifying plain "text" regions
_QUESTION_PATTERNS = [
    re.compile(r"^\d+[\.\)]\s"),
    re.compile(r"^[A-Z][\.\)]\s"),
    re.compile(r"^Q\d+"),
    re.compile(r"^Question\s+\d+", re.IGNORECASE),
]
_INSTRUCTION_PATTERNS = [
    re.compile(r"^(Read|Write|Circle|Tick|Match|Fill|Choose|Answer|Look|Complete|Draw)", re.IGNORECASE),
    re.compile(r"^Instructions?:", re.IGNORECASE),
]
_BLANK_PATTERNS = [
    re.compile(r"_{3,}"),
    re.compile(r"\[\s+\]"),
    re.compile(r"☐|□"),
]


def _classify_text_region(text: str) -> RegionType:
    first_line = text.strip().split("\n")[0] if text.strip() else ""
    for pat in _QUESTION_PATTERNS:
        if pat.search(first_line):
            return RegionType.QUESTION
    for pat in _INSTRUCTION_PATTERNS:
        if pat.search(first_line):
            return RegionType.INSTRUCTION
    for pat in _BLANK_PATTERNS:
        if pat.search(text):
            return RegionType.BLANK_LINE
    return RegionType.TEXT_BLOCK


def _parse_bbox(bbox_raw) -> list[float]:
    """
    Normalise bbox to [x1, y1, x2, y2].
    PaddleOCR 3.x LayoutDetection returns bboxes as [x1, y1, x2, y2] lists.
    """
    if isinstance(bbox_raw, (list, np.ndarray)):
        flat = np.array(bbox_raw, dtype=float).flatten()
        if len(flat) == 4:
            return flat.tolist()
        if len(flat) == 8:
            # 4-point polygon
            xs = flat[0::2]
            ys = flat[1::2]
            return [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]
    return [0.0, 0.0, 0.0, 0.0]


class LayoutDetector:
    """
    Wraps PaddleOCR 3.x LayoutDetection for page region detection.

    Models are downloaded on first use (~200 MB).
    """

    def __init__(self, lang: str = "en"):
        self._lang = lang
        self._layout_engine = None
        self._ocr_engine = None

    def _get_layout_engine(self):
        if self._layout_engine is None:
            logger.info("Initialising PaddleOCR LayoutDetection …")
            from paddleocr import LayoutDetection
            self._layout_engine = LayoutDetection()
            logger.info("LayoutDetection ready.")
        return self._layout_engine

    def _get_ocr_engine(self):
        if self._ocr_engine is None:
            logger.info("Initialising PaddleOCR (lang=%s) for layout OCR …", self._lang)
            from paddleocr import PaddleOCR
            self._ocr_engine = PaddleOCR(
                lang=self._lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            logger.info("PaddleOCR for layout ready.")
        return self._ocr_engine

    def detect(
        self,
        img: np.ndarray,
        page_number: int = 1,
    ) -> list[LayoutRegion]:
        """
        Run layout detection on a BGR image.
        Returns LayoutRegion objects in reading order.
        """
        h, w = img.shape[:2]

        raw_regions = self._run_layout_detection(img, h, w)

        # Sort into reading order
        is_two_col = _guess_column_count(raw_regions, w) == 2
        ordered = sort_regions_reading_order(
            raw_regions,
            n_columns=2 if is_two_col else 1,
        )

        layout_regions: list[LayoutRegion] = []
        for idx, r in enumerate(ordered):
            region_id = f"p{page_number}_r{idx:03d}"
            layout_regions.append(
                LayoutRegion(
                    region_id=region_id,
                    region_type=r["region_type"],
                    bbox=r["bbox"],
                    page_number=page_number,
                    confidence=r.get("confidence", 0.85),
                    raw_layout_label=r.get("raw_label", ""),
                )
            )

        logger.info(
            "Page %d: detected %d regions (%s)",
            page_number, len(layout_regions),
            "2-col" if is_two_col else "1-col",
        )
        return layout_regions

    def _run_layout_detection(
        self, img: np.ndarray, h: int, w: int
    ) -> list[dict]:
        """Run LayoutDetection and parse results into dicts."""
        try:
            engine = self._get_layout_engine()
            results = engine.predict(img)

            raw_regions: list[dict] = []
            for result in results:
                # PaddleOCR 3.x predict() returns an iterable of result objects
                boxes = result.get("boxes", []) if isinstance(result, dict) else []
                if not boxes and hasattr(result, "__iter__"):
                    # Some versions return list of dicts directly
                    boxes = list(result)

                for box in boxes:
                    if isinstance(box, dict):
                        label = str(box.get("label", box.get("cls_name", "text"))).lower()
                        bbox_raw = box.get("coordinate", box.get("bbox", box.get("box", [0, 0, w, h])))
                        score = float(box.get("score", box.get("confidence", 0.8)))
                    else:
                        continue

                    bbox = _parse_bbox(bbox_raw)
                    region_type = _LABEL_MAP.get(label, RegionType.TEXT_BLOCK)
                    raw_regions.append({
                        "bbox": bbox,
                        "region_type": region_type,
                        "raw_label": label,
                        "confidence": score,
                    })

            if raw_regions:
                return raw_regions

        except Exception as exc:
            logger.warning("LayoutDetection failed (%s) — falling back to OCR-based regions", exc)

        # Fallback: use PaddleOCR text detection to find text regions,
        # treat each line cluster as a TEXT_BLOCK region.
        return self._ocr_based_regions(img, h, w)

    def _ocr_based_regions(self, img: np.ndarray, h: int, w: int) -> list[dict]:
        """
        Fallback: run PaddleOCR on the full page and cluster text lines
        into approximate block regions. This is less accurate than LayoutDetection
        but always works.
        """
        logger.info("Using OCR-based region detection fallback")
        try:
            ocr = self._get_ocr_engine()
            raw = ocr.predict(img)

            regions = []
            for page_result in raw:
                rec_texts = page_result.get("rec_texts", [])
                rec_boxes = page_result.get("det_polys", page_result.get("rec_boxes", []))
                rec_scores = page_result.get("rec_scores", [])

                for i, (text, bbox_raw) in enumerate(zip(rec_texts, rec_boxes)):
                    if not text or not text.strip():
                        continue
                    bbox = _parse_bbox(bbox_raw)
                    score = float(rec_scores[i]) if i < len(rec_scores) else 0.8
                    region_type = _classify_text_region(text)
                    regions.append({
                        "bbox": bbox,
                        "region_type": region_type,
                        "raw_label": "text",
                        "confidence": score,
                        "ocr_text": text,
                    })

            if regions:
                return regions
        except Exception as exc:
            logger.error("OCR-based fallback also failed: %s", exc)

        # Last resort: single full-page region
        logger.warning("All layout detection failed — using full-page region")
        return [{
            "bbox": [0.0, 0.0, float(w), float(h)],
            "region_type": RegionType.TEXT_BLOCK,
            "raw_label": "full_page_fallback",
            "confidence": 0.3,
        }]


def _guess_column_count(regions: list[dict], page_width: int) -> int:
    if not regions or page_width == 0 or len(regions) < 4:
        return 1
    mid = page_width / 2
    left = sum(1 for r in regions if (r["bbox"][0] + r["bbox"][2]) / 2 < mid)
    right = sum(1 for r in regions if (r["bbox"][0] + r["bbox"][2]) / 2 >= mid)
    total = len(regions)
    if left / total > 0.25 and right / total > 0.25:
        return 2
    return 1
