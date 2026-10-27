"""
OCR engine wrapper — updated for PaddleOCR 3.x.

PaddleOCR 3.x API changes:
  - Old:  ocr.ocr(img, cls=True)  → returns list of [[bbox, (text, conf)], ...]
  - New:  ocr.predict(img)        → returns iterable of result dicts with keys:
            rec_texts, rec_scores, det_polys / rec_boxes
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from app.services.ocr.schemas.homework import OCRResult, LayoutRegion, ReviewFlag, ReviewReason

logger = logging.getLogger(__name__)


def _parse_bbox_ocr(bbox_raw) -> list[float]:
    """Convert any bbox format to [x1, y1, x2, y2]."""
    arr = np.array(bbox_raw, dtype=float).flatten()
    if len(arr) == 4:
        return arr.tolist()
    if len(arr) >= 8:
        xs = arr[0::2]
        ys = arr[1::2]
        return [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]
    return [0.0, 0.0, 0.0, 0.0]


class OCREngine:
    """
    PaddleOCR 3.x wrapper.
    Engine is lazy-initialised on first use.
    """

    def __init__(self, lang: str = "en", confidence_threshold: float = 0.70):
        self._lang = lang
        self._threshold = confidence_threshold
        self._ocr = None

    def _get_engine(self):
        if self._ocr is None:
            logger.info("Initialising PaddleOCR 3.x (lang=%s) …", self._lang)
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                lang=self._lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            logger.info("PaddleOCR 3.x ready.")
        return self._ocr

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run_on_image(
        self,
        img: np.ndarray,
        page_number: int = 1,
        region_id: Optional[str] = None,
    ) -> list[OCRResult]:
        """
        Run OCR on a BGR image (full page or cropped region).
        Returns list of OCRResult objects.
        """
        ocr = self._get_engine()
        results: list[OCRResult] = []

        try:
            raw = ocr.predict(img)
        except Exception as exc:
            logger.error("PaddleOCR predict() error: %s", exc)
            return results

        for page_result in raw:
            if page_result is None:
                continue

            texts = page_result.get("rec_texts", []) or []
            scores = page_result.get("rec_scores", []) or []
            # Bounding boxes — safely handle numpy array / list
            boxes = []
            for k in ("det_polys", "rec_boxes", "dt_polys"):
                val = page_result.get(k)
                if val is not None and len(val) > 0:
                    boxes = val
                    break

            for i, text in enumerate(texts):
                if not text or not text.strip():
                    continue
                conf = float(scores[i]) if i < len(scores) else 0.8
                bbox_raw = boxes[i] if i < len(boxes) else [0, 0, 0, 0]
                bbox = _parse_bbox_ocr(bbox_raw)

                results.append(OCRResult(
                    text=text.strip(),
                    bbox=bbox,
                    confidence=conf,
                    page_number=page_number,
                    region_id=region_id,
                ))

        low_conf = [r for r in results if r.confidence < self._threshold]
        if low_conf:
            logger.debug(
                "Region %s: %d/%d results below threshold %.2f",
                region_id, len(low_conf), len(results), self._threshold,
            )

        return results

    def run_on_regions(
        self,
        img: np.ndarray,
        regions: list[LayoutRegion],
        page_number: int = 1,
    ) -> list[LayoutRegion]:
        """
        Run OCR on each text/table region and attach results.
        Figure/Diagram/Graph regions are skipped (handled by VLM).
        Modifies regions in-place and returns the list.
        """
        from app.services.ocr.schemas.homework import RegionType
        from app.services.ocr.utils.image_utils import crop_region

        SKIP_TYPES = {RegionType.FIGURE, RegionType.DIAGRAM, RegionType.GRAPH}

        for region in regions:
            if region.region_type in SKIP_TYPES:
                continue

            crop = crop_region(img, region.bbox)
            if crop.size == 0:
                continue

            ocr_results = self.run_on_image(
                crop, page_number=page_number, region_id=region.region_id
            )

            # Offset bboxes back to full-page coordinates
            x_off, y_off = region.bbox[0], region.bbox[1]
            for r in ocr_results:
                r.bbox = [
                    r.bbox[0] + x_off, r.bbox[1] + y_off,
                    r.bbox[2] + x_off, r.bbox[3] + y_off,
                ]

            region.ocr_results = ocr_results

            if ocr_results:
                avg_conf = sum(r.confidence for r in ocr_results) / len(ocr_results)
                if avg_conf < self._threshold:
                    region.review = ReviewFlag(
                        reason=ReviewReason.LOW_OCR_CONFIDENCE,
                        detail=f"Avg OCR confidence {avg_conf:.2f}",
                    )
                    region.confidence = avg_conf
            else:
                region.review = ReviewFlag(
                    reason=ReviewReason.LOW_OCR_CONFIDENCE,
                    detail="No text detected by OCR",
                )
                region.confidence = 0.3

        return regions

    def full_text(self, region: LayoutRegion) -> str:
        return " ".join(r.text for r in region.ocr_results).strip()
