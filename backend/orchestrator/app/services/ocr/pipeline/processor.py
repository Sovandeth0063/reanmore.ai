"""
Main pipeline orchestrator.

Connects all pipeline stages in order:
  1. Input handling (image or PDF)
  2. Image preprocessing
  3. Layout detection
  4. OCR
  5. Visual processing (figure crops)
  6. VLM analysis
  7. Schema assembly
  8. Validation
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, Union

import numpy as np

from app.services.ocr.config import settings
from app.services.ocr.schemas.homework import (
    DocumentMeta, HomeworkResponse, Page,
)
from app.services.ocr.preprocessing.image_prep import preprocess_image
from app.services.ocr.layout.layout_detector import LayoutDetector
from app.services.ocr.ocr.ocr_engine import OCREngine
from app.services.ocr.vision.visual_processor import VisualProcessor
from app.services.ocr.validation.validator import Validator
from app.services.ocr.utils.image_utils import ndarray_to_base64, get_image_dimensions
from app.services.ocr.utils.bbox_utils import convert_bboxes_to_pixels

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0.0"


class HomeworkProcessor:
    """
    Singleton-style orchestrator.  Initialise once and reuse for multiple requests.

    All heavy models (PaddleOCR, PP-Structure, Gemini) are loaded lazily on
    first use.
    """

    def __init__(self):
        self._layout_detector = None   # lazy — only created when USE_LAYOUT_REGIONS=true
        self._ocr_engine = None
        self._visual_processor = VisualProcessor()
        self._validator = Validator(confidence_threshold=settings.low_confidence_threshold)
        self._vlm = self._build_vlm()

    def _ensure_layout_models(self):
        """Initialise layout/OCR models on first use."""
        if self._layout_detector is None:
            self._layout_detector = LayoutDetector(lang=settings.layout_lang)
        if self._ocr_engine is None:
            self._ocr_engine = OCREngine(
                lang=settings.layout_lang,
                confidence_threshold=settings.ocr_confidence_threshold,
            )

    def _build_single_vlm(self, provider: str, model: str, api_key: str = "", base_url: str = ""):
        p = provider.lower()
        if p == "gemini":
            from app.services.ocr.vlm.gemini_vlm import GeminiVLM
            return GeminiVLM(api_key=api_key or settings.gemini_api_key, model_name=model)
        if p == "ollama":
            from app.services.ocr.vlm.ollama_vlm import OllamaVLM
            return OllamaVLM(
                api_key=api_key or settings.ollama_api_key,
                model_name=model,
                base_url=base_url or settings.ollama_base_url,
            )
        raise ValueError(f"Unknown VLM provider: {p!r}. Supported: gemini, ollama")

    def _build_vlm(self):
        """Construct the configured primary and fallback VLM providers."""
        primary = self._build_single_vlm(
            provider=settings.vlm_provider,
            model=settings.vlm_model,
            api_key=settings.gemini_api_key if settings.vlm_provider.lower() == "gemini" else settings.ollama_api_key,
            base_url=settings.ollama_base_url,
        )
        fb_provider = getattr(settings, "vlm_fallback_provider", "").strip().lower()
        if fb_provider and fb_provider != "none":
            from app.services.ocr.vlm.resilient_vlm import ResilientVLM
            fallback = self._build_single_vlm(
                provider=fb_provider,
                model=getattr(settings, "vlm_fallback_model", "gemma4:31b"),
                api_key=getattr(settings, "ollama_fallback_api_key", "") or settings.ollama_api_key,
                base_url=getattr(settings, "ollama_fallback_base_url", "") or settings.ollama_base_url,
            )
            return ResilientVLM(primary=primary, fallback=fallback)
        return primary

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def process(
        self,
        file_bytes: bytes,
        filename: str,
        save_debug_crops: bool = False,
    ) -> HomeworkResponse:
        """
        Full pipeline: bytes → HomeworkResponse.

        Args:
            file_bytes:        Raw bytes of the uploaded file.
            filename:          Original filename (used to detect PDF vs image).
            save_debug_crops:  If True, save cropped regions to sample_outputs/.

        Returns:
            Fully populated HomeworkResponse.
        """
        start_time = time.perf_counter()
        suffix = Path(filename).suffix.lower()

        # --- Step 1: Load image(s) ---
        images = self._load_images(file_bytes, suffix)
        logger.info("Loaded %d page(s) from '%s'", len(images), filename)

        # --- Steps 2-7: Process each page ---
        pages: list[Page] = []
        stage_times: dict[str, float] = {"preprocess": 0.0, "layout_ocr": 0.0, "vlm": 0.0}
        for page_idx, img in enumerate(images):
            page_number = page_idx + 1
            logger.info("--- Processing page %d / %d ---", page_number, len(images))
            page, page_stages = self._process_page(img, page_number, save_debug_crops)
            pages.append(page)
            for k, v in page_stages.items():
                stage_times[k] = stage_times.get(k, 0.0) + v

        # --- Step 8: Assemble document ---
        page_confs = [p.confidence for p in pages if p.confidence is not None]
        overall_confidence = min(page_confs) if page_confs else None
        meta = getattr(pages[0], "_meta", {}) if pages else {}
        doc_title = meta.get("title") or self._infer_title(pages)
        doc_subject = meta.get("subject")
        doc_grade = meta.get("grade_level")
        doc_lang = meta.get("language") or ["English"]

        response = HomeworkResponse(
            status="success",
            document=DocumentMeta(
                title=doc_title,
                language=doc_lang,
                pages=len(pages),
                subject=doc_subject,
                grade_level=doc_grade,
            ),
            pages=pages,
            confidence=round(overall_confidence, 3) if overall_confidence is not None else None,
            pipeline_version=PIPELINE_VERSION,
            bbox_unit="px",   # Item 5: bboxes are pixel coords after conversion
        )

        # --- Step 9: Validation ---
        t_val_start = time.perf_counter()
        validation = self._validator.validate(response)
        stage_times["validation"] = round(time.perf_counter() - t_val_start, 3)
        response.validation = validation

        elapsed = time.perf_counter() - start_time
        response.processing_time_seconds = round(elapsed, 2)
        response.stage_timers = {k: round(v, 3) for k, v in stage_times.items()}
        logger.info(
            "Pipeline complete: %d pages, confidence=%s, time=%.1fs, stages=%s",
            len(pages), overall_confidence, elapsed, response.stage_timers,
        )
        return response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_images(self, file_bytes: bytes, suffix: str) -> list[np.ndarray]:
        """Convert file bytes to a list of BGR NumPy images."""
        import io
        import tempfile
        import cv2

        if suffix == ".pdf":
            from app.services.ocr.utils.pdf_utils import pdf_to_images
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = Path(tmp.name)
            try:
                return pdf_to_images(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)

        # Image file
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Could not decode image (suffix={suffix})")
        return [img]

    def _process_page(
        self,
        img: np.ndarray,
        page_number: int,
        save_debug_crops: bool,
    ) -> tuple[Page, dict[str, float]]:
        """Run the full pipeline on a single page image. Returns (page, stage_times)."""
        stage_times: dict[str, float] = {}

        # 2. Preprocessing
        t0 = time.perf_counter()
        prep = preprocess_image(
            img,
            max_long_side=settings.max_image_long_side,
        )
        proc_img = prep.processed_image
        orig_img = prep.original_image
        stage_times["preprocess"] = round(time.perf_counter() - t0, 3)

        w, h = get_image_dimensions(proc_img)

        # 3 & 4. Layout detection + OCR  (skipped when USE_LAYOUT_REGIONS=false)
        if settings.use_layout_regions:
            t0 = time.perf_counter()
            self._ensure_layout_models()
            regions = self._layout_detector.detect(proc_img, page_number=page_number)
            regions = self._ocr_engine.run_on_regions(proc_img, regions, page_number=page_number)
            stage_times["layout_ocr"] = round(time.perf_counter() - t0, 3)
            # 5. Visual processing (crop figures for VLM)
            if save_debug_crops:
                debug_dir = Path("sample_outputs") / f"page_{page_number}"
                self._visual_processor._save_dir = debug_dir
            regions = self._visual_processor.process_regions(proc_img, regions)
        else:
            regions = []
            stage_times["layout_ocr"] = 0.0
            logger.info("Page %d: layout/OCR skipped (USE_LAYOUT_REGIONS=false)", page_number)

        # 6. Encode page images for VLM
        proc_b64 = "data:image/png;base64," + ndarray_to_base64(proc_img)
        orig_b64 = "data:image/png;base64," + ndarray_to_base64(orig_img)

        # 7. VLM analysis
        t0 = time.perf_counter()
        page = self._vlm.analyze_page(
            page_image_b64=proc_b64,
            regions=regions,
            page_number=page_number,
            original_image_b64=orig_b64,
        )
        # Collect VLM timer stashed by provider (fallback to wall time)
        stage_times["vlm"] = round(
            getattr(page, "_t_vlm", time.perf_counter() - t0), 3
        )

        page.width = w
        page.height = h

        # Item 5: convert answer_area bboxes from 0-1000 to pixels
        convert_bboxes_to_pixels(page, w, h)

        # Item 6: when use_layout_regions=False, clear regions from response
        if not settings.use_layout_regions:
            page.regions = []

        return page, stage_times

    def _infer_title(self, pages: list[Page]) -> Optional[str]:
        """Try to find a title from header, banner directions, or regions."""
        if not pages:
            return None
        first_page = pages[0]
        if first_page.header and first_page.header.school:
            return first_page.header.school
        if first_page.directions:
            for d in first_page.directions:
                if not d.label and d.text and len(d.text) < 120:
                    return d.text
        from app.services.ocr.schemas.homework import RegionType
        for region in first_page.regions:
            if region.region_type == RegionType.HEADER and region.ocr_results:
                return region.ocr_results[0].text
        return None
