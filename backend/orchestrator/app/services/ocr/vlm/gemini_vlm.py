"""
Gemini Vision VLM provider — uses the new google-genai SDK.
The extraction prompt and all parsing logic live in prompt_parser.py.

Changes: Item 1 (prompt/response logging), Item 7 (t_vlm timer).
"""
from __future__ import annotations

import base64
import hashlib
import logging
import time
from typing import Optional

from app.services.ocr.config import settings
from app.services.ocr.vlm.base import VLMProvider
from app.services.ocr.vlm.prompt_parser import (
    PAGE_ANALYSIS_PROMPT, FIGURE_DESCRIPTION_PROMPT,
    build_ocr_context, extract_json,
    parse_vlm_response, make_error_page,
)
from app.services.ocr.schemas.homework import LayoutRegion, Page, RegionType

logger = logging.getLogger(__name__)


class GeminiVLM(VLMProvider):
    """Google Gemini Vision provider using the new google-genai SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash"):
        from google import genai
        from google.genai import types as genai_types
        self._client = genai.Client(api_key=api_key)
        
        # Google deprecates older models for new API keys; map seamlessly to fastest available flash model
        alias_map = {
            "gemini-2.5-flash": "gemini-3.5-flash",
            "gemini-2.5-flash-lite": "gemini-3.5-flash",
            "gemini-2.0-flash": "gemini-3.5-flash",
            "gemini-flash-latest": "gemini-3.5-flash",
            "gemini-flash-lite-latest": "gemini-3.5-flash",
        }
        self._model_name = alias_map.get(model_name, model_name)
        self._genai_types = genai_types
        self._prompt_hash = hashlib.sha256(PAGE_ANALYSIS_PROMPT.encode()).hexdigest()[:12]
        logger.info(
            "GeminiVLM initialised (requested=%s, model=%s, sdk=google-genai, prompt_hash=%s)",
            model_name, self._model_name, self._prompt_hash,
        )

    def _image_part(self, data_uri: str):
        """Convert a base64 data URI to a genai Part."""
        header, b64data = data_uri.split(",", 1)
        mime = header.split(":")[1].split(";")[0]
        image_bytes = base64.b64decode(b64data)
        return self._genai_types.Part.from_bytes(data=image_bytes, mime_type=mime)

    def _call_model(self, contents: list, max_retries: int = 2) -> str:
        """Call Gemini with automatic model failover if a model encounters temporary demand spikes (503)."""
        candidate_models = [self._model_name]
        for m in ["gemini-3.5-flash", "gemini-3.6-flash"]:
            if m not in candidate_models:
                candidate_models.append(m)

        last_exc = None
        for model in candidate_models:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info("Attempting Gemini model '%s' (attempt %d/%d)...", model, attempt, max_retries)
                    response = self._client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=self._genai_types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=8192,
                            thinking_config=self._genai_types.ThinkingConfig(thinking_budget=0),
                        ),
                    )
                    return response.text
                except Exception as exc:
                    logger.warning("Gemini model '%s' attempt %d/%d failed: %s", model, attempt, max_retries, exc)
                    last_exc = exc
                    if attempt < max_retries:
                        time.sleep(1.0)
                    else:
                        break  # move to next candidate model

        if last_exc:
            raise last_exc
        raise RuntimeError("No candidate Gemini models succeeded")

    def analyze_page(
        self,
        page_image_b64: str,
        regions: list[LayoutRegion],
        page_number: int = 1,
        original_image_b64: Optional[str] = None,
    ) -> Page:
        ocr_context = build_ocr_context(regions)
        prompt_text = PAGE_ANALYSIS_PROMPT.format(ocr_context=ocr_context)

        # Item 1: log prompt sent
        if settings.log_vlm_io:
            logger.info(
                "Prompt sent to Gemini (page %d): hash=%s | first 400 chars:\n%s",
                page_number,
                hashlib.sha256(prompt_text.encode()).hexdigest()[:12],
                prompt_text[:400],
            )

        contents = [self._image_part(page_image_b64), prompt_text]
        figure_count = 0
        for region in regions:
            if (region.image_reference and region.region_type == RegionType.FIGURE
                    and figure_count < 3):
                contents.append(f"\n[Figure crop {region.region_id}]:")
                contents.append(self._image_part(region.image_reference))
                figure_count += 1

        logger.info("Sending page %d to Gemini (%d regions) ...", page_number, len(regions))

        # Item 7: time the model call
        t0 = time.perf_counter()
        try:
            raw_text = self._call_model(contents)
        except Exception as exc:
            logger.error("Gemini call failed for page %d: %s", page_number, exc)
            return make_error_page(page_number, regions, f"Gemini API error: {exc}")
        t_vlm = time.perf_counter() - t0

        # Item 1: log raw response
        if settings.log_vlm_io:
            logger.debug("Gemini raw response (page %d, %.1fs):\n%s", page_number, t_vlm, raw_text)
        else:
            logger.debug("Gemini raw response (first 500): %s", raw_text[:500])

        try:
            data = extract_json(raw_text)
        except (ValueError, Exception) as exc:
            logger.error("Failed to parse Gemini JSON response: %s", exc)
            return make_error_page(page_number, regions, f"VLM JSON parse error: {exc}")

        page = parse_vlm_response(data, page_number, regions)
        page._t_vlm = t_vlm  # type: ignore[attr-defined]
        logger.info(
            "Page %d analysed by Gemini: %d sections, confidence=%s, vlm=%.1fs",
            page_number, len(page.sections), page.confidence, t_vlm,
        )
        return page


    def describe_figure(self, figure_b64: str, context: Optional[str] = None) -> dict:
        prompt = FIGURE_DESCRIPTION_PROMPT.format(context=context or "")
        contents = [self._image_part(figure_b64), prompt]
        try:
            raw = self._call_model(contents)
            return extract_json(raw)
        except Exception as exc:
            logger.error("Figure description failed: %s", exc)
            return {"description": "Could not describe figure", "confidence": 0.0}

    def provider_name(self) -> str:
        return f"GeminiVLM({self._model_name})"
