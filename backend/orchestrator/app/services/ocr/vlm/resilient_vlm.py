"""Resilient VLM provider with transparent primary -> fallback switching.

Executes primary VLM (e.g. Gemini Flash for ~2s speed) and automatically
falls back to secondary VLM (e.g. Ollama gemma4:31b for 100% reliability)
if the primary fails, encounters 503/rate limits, or returns 0 questions.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.services.ocr.schemas.homework import LayoutRegion, Page
from app.services.ocr.vlm.base import VLMProvider

logger = logging.getLogger(__name__)


class ResilientVLM(VLMProvider):
    """
    Composite VLM provider that attempts primary provider first,
    and falls back to secondary provider on any failure or empty extraction.
    """

    def __init__(self, primary: VLMProvider, fallback: Optional[VLMProvider] = None):
        self.primary = primary
        self.fallback = fallback
        p_name = self.primary.provider_name() if hasattr(self.primary, "provider_name") else type(self.primary).__name__
        f_name = self.fallback.provider_name() if self.fallback and hasattr(self.fallback, "provider_name") else (type(self.fallback).__name__ if self.fallback else "None")
        logger.info("ResilientVLM initialized (primary=%s, fallback=%s)", p_name, f_name)

    def _is_failed_page(self, page: Page) -> bool:
        """Check if returned page is an error or empty extraction."""
        if not page.sections:
            return True
        total_questions = sum(len(s.questions) for s in page.sections)
        if total_questions == 0:
            return True
        if page.confidence is not None and page.confidence <= 0.15:
            return True
        for sec in page.sections:
            for q in sec.questions:
                if q.prompt and ("api error" in q.prompt.lower() or "not_found" in q.prompt.lower()):
                    return True
        return False

    def analyze_page(
        self,
        page_image_b64: str,
        regions: list[LayoutRegion],
        page_number: int = 1,
        original_image_b64: Optional[str] = None,
    ) -> Page:
        page = None
        try:
            logger.info("ResilientVLM: Attempting primary VLM analysis on page %d...", page_number)
            page = self.primary.analyze_page(
                page_image_b64=page_image_b64,
                regions=regions,
                page_number=page_number,
                original_image_b64=original_image_b64,
            )
            if not self._is_failed_page(page):
                return page
            logger.warning(
                "ResilientVLM: Primary VLM returned unusable/error page on page %d. Engaging fallback...",
                page_number,
            )
        except Exception as exc:
            logger.warning(
                "ResilientVLM: Primary VLM encountered error (%s). Engaging fallback...",
                exc,
            )

        if self.fallback is not None:
            logger.info("ResilientVLM: Executing fallback VLM analysis on page %d...", page_number)
            fallback_page = self.fallback.analyze_page(
                page_image_b64=page_image_b64,
                regions=regions,
                page_number=page_number,
                original_image_b64=original_image_b64,
            )
            fallback_page.warnings.append("Processed by fallback VLM provider")
            return fallback_page

        return page if page is not None else Page(page_number=page_number, sections=[], confidence=0.0)

    def describe_figure(
        self,
        figure_b64: str,
        context: Optional[str] = None,
    ) -> dict:
        try:
            res = self.primary.describe_figure(figure_b64, context)
            if res and res.get("description") and "error" not in res.get("description", "").lower():
                return res
        except Exception as exc:
            logger.warning("Primary figure description failed (%s). Trying fallback...", exc)

        if self.fallback:
            return self.fallback.describe_figure(figure_b64, context)
        return {"description": "Could not describe figure", "confidence": 0.0}

    def provider_name(self) -> str:
        p_name = self.primary.provider_name() if hasattr(self.primary, "provider_name") else type(self.primary).__name__
        f_name = self.fallback.provider_name() if self.fallback and hasattr(self.fallback, "provider_name") else "None"
        return f"ResilientVLM(primary={p_name}, fallback={f_name})"
