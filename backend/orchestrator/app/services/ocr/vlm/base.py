"""
Abstract VLM provider interface.

Any Vision-Language Model integration must implement this interface,
making the provider swappable (Gemini → Claude → Qwen-VL, etc.).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from app.services.ocr.schemas.homework import LayoutRegion, Page


class VLMProvider(ABC):
    """
    Abstract base for VLM providers.

    Each provider receives page images + OCR context and must return a
    structured Page object with questions, elements, and confidence scores.
    """

    @abstractmethod
    def analyze_page(
        self,
        page_image_b64: str,
        regions: list[LayoutRegion],
        page_number: int = 1,
        original_image_b64: Optional[str] = None,
    ) -> Page:
        """
        Analyse a single homework page.

        Args:
            page_image_b64:    Base64 data URI of the processed page image.
            regions:           Layout regions with OCR text and visual crops.
            page_number:       1-based page index.
            original_image_b64: Optional base64 of the unprocessed original.

        Returns:
            A fully-populated Page object.
        """
        ...

    @abstractmethod
    def describe_figure(
        self,
        figure_b64: str,
        context: Optional[str] = None,
    ) -> dict:
        """
        Describe a single visual region (figure, diagram, graph).

        Args:
            figure_b64: Base64 data URI of the cropped region.
            context:    Surrounding text context to help the VLM.

        Returns:
            Dict with at least: {"description": str, "confidence": float}
        """
        ...

    def provider_name(self) -> str:
        return self.__class__.__name__
