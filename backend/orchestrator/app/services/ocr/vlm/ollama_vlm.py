"""
Ollama Vision VLM provider.

Calls the Ollama remote API (https://ollama.com/api/chat) using
Bearer-token authentication. Supports multimodal models (e.g. gemma4:31b).
The extraction prompt and all parsing logic live in prompt_parser.py.

Changes vs original:
  - Item 1: logs exact prompt sent (truncated) and full raw response
  - Item 2: adds Ollama `format` JSON schema; retries once on parse failure
  - Item 7: honours VLM_DISABLE_THINKING config flag; records t_vlm timer
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Optional

import httpx

from app.services.ocr.config import settings
from app.services.ocr.vlm.base import VLMProvider
from app.services.ocr.vlm.prompt_parser import (
    PAGE_ANALYSIS_PROMPT, FIGURE_DESCRIPTION_PROMPT,
    build_ocr_context, extract_json,
    parse_vlm_response, make_error_page, _norm_kind,
)
from app.services.ocr.schemas.homework import LayoutRegion, Page, RegionType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ollama structured-output schema (enforces type and kind enums)
# ---------------------------------------------------------------------------
_OLLAMA_FORMAT_SCHEMA = {
    "type": "object",
    "properties": {
        "header": {"type": ["object", "null"]},
        "directions": {"type": "array"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "title": {"type": ["string", "null"]},
                    "instructions": {"type": ["string", "null"]},
                    "figure": {"type": ["object", "null"]},
                    "elements": {"type": ["array", "null"]},
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "number_printed": {"type": "string"},
                                "type": {
                                    "type": "string",
                                    "enum": [
                                        "fill_blank", "equation", "match", "circle",
                                        "tick", "table", "draw", "order",
                                        "multiple_choice", "short_answer", "other",
                                    ],
                                },
                                "prompt": {"type": ["string", "null"]},
                                "instructions": {"type": ["string", "null"]},
                                "elements": {
                                    "type": ["array", "null"],
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string"},
                                            "text": {"type": "string"},
                                            "left_item": {"type": "string"},
                                            "right_item": {"type": "string"},
                                            "bbox": {
                                                "type": "array",
                                                "items": {"type": "integer"},
                                            },
                                        },
                                    },
                                },
                                "figure": {"type": ["object", "null"]},
                                "answer_areas": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "kind": {
                                                "type": "string",
                                                "enum": [
                                                    "blank_line", "blank_box",
                                                    "table_cell", "tick_box",
                                                    "circle", "dot",
                                                ],
                                            },
                                            "bbox": {
                                                "type": "array",
                                                "items": {"type": "integer"},
                                                "minItems": 4,
                                                "maxItems": 4,
                                            },
                                        },
                                    },
                                },
                                "student_answer": {},
                                "matches": {"type": ["array", "null"]},
                                "confidence": {"type": "number"},
                            },
                            "required": ["id", "number_printed", "type", "prompt",
                                         "answer_areas", "confidence"],
                        },
                    },
                },
            },
        },
        "footer": {"type": ["object", "null"]},
        "confidence": {"type": "number"},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["sections", "warnings"],
}


class OllamaVLM(VLMProvider):
    """
    Vision-Language Model provider backed by a remote Ollama server.
    Sends base64-encoded images + text prompts via Bearer-token auth.
    Compatible with multimodal Ollama models such as gemma4:31b.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemma4:31b",
        base_url: str = "https://ollama.com",
        timeout: float = 120.0,
    ):
        self._api_key = api_key
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {
            "Content-Type": "application/json",
        }
        if api_key and api_key.strip():
            self._headers["Authorization"] = f"Bearer {api_key.strip()}"
        # Compute hash of the in-memory prompt for drift detection (Item 1)
        self._prompt_hash = hashlib.sha256(PAGE_ANALYSIS_PROMPT.encode()).hexdigest()[:12]
        logger.info(
            "OllamaVLM initialised (model=%s, base_url=%s, prompt_hash=%s)",
            model_name, base_url, self._prompt_hash,
        )

    @staticmethod
    def _strip_data_uri(data_uri: str) -> str:
        """Strip the data:image/...;base64, prefix — Ollama wants raw base64."""
        if "," in data_uri:
            return data_uri.split(",", 1)[1]
        return data_uri

    def _call_model(self, prompt: str, images_b64: list, max_retries: int = 3) -> str:
        """POST to /api/chat and return the assistant content string."""
        raw_images = [self._strip_data_uri(img) for img in images_b64]
        message: dict = {"role": "user", "content": prompt}
        if raw_images:
            message["images"] = raw_images

        payload: dict = {
            "model": self._model_name,
            "messages": [message],
            "stream": False,
            "format": _OLLAMA_FORMAT_SCHEMA,   # structured output
            "options": {
                "temperature": 0,              # Item 1: deterministic
                "seed": settings.vlm_seed,     # Item 1: fixed seed
            },
        }
        if settings.vlm_disable_thinking:
            payload["think"] = False

        # Item 1: log exact request (replace image bytes with size summary)
        if settings.log_vlm_io:
            loggable = {k: v for k, v in payload.items() if k != "messages"}
            loggable["messages"] = [{
                "role": message["role"],
                "content": f"<prompt {len(prompt)} chars>",
                "images": f"<{len(raw_images)} image(s)>",
            }]
            logger.info(
                "Ollama request payload (temperature=0, seed=%d): %s",
                settings.vlm_seed,
                json.dumps(loggable, ensure_ascii=False, indent=None),
            )

        url = f"{self._base_url}/api/chat"

        for attempt in range(1, max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content") or data.get("response") or ""
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Ollama HTTP %d on attempt %d/%d: %s",
                    exc.response.status_code, attempt, max_retries, exc,
                )
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise
            except Exception as exc:
                logger.warning("Ollama attempt %d/%d failed: %s", attempt, max_retries, exc)
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def _try_parse(
        self,
        raw_text: str,
        page_number: int,
        regions: list[LayoutRegion],
        strict_enums: bool = False,
    ) -> Optional[Page]:
        """
        Attempt to extract JSON and parse into a Page.
        If strict_enums is True, rejects payloads with invalid type/kind to force a retry.
        Returns None on any failure (caller will retry once then give up).
        """
        try:
            data = extract_json(raw_text)
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("JSON parse error (page %d): %s", page_number, exc)
            return None

        if strict_enums:
            from app.services.ocr.schemas.homework import ALLOWED_QUESTION_TYPES, QUESTION_KINDS
            for sec in data.get("sections", []) if isinstance(data, dict) else []:
                if not isinstance(sec, dict):
                    continue
                for q in sec.get("questions", []):
                    if not isinstance(q, dict):
                        continue
                    t = str(q.get("type", "")).lower().strip()
                    if t and t not in ALLOWED_QUESTION_TYPES:
                        logger.warning(
                            "Attempt 1 rejected: invalid question type %r (allowed: %s)",
                            t, sorted(ALLOWED_QUESTION_TYPES),
                        )
                        return None
                    for area in q.get("answer_areas", []):
                        if isinstance(area, dict):
                            k = _norm_kind(area.get("kind", ""))
                            if k and k not in QUESTION_KINDS:
                                logger.warning(
                                    "Attempt 1 rejected: invalid answer_area kind %r (allowed: %s)",
                                    k, sorted(QUESTION_KINDS),
                                )
                                return None

        try:
            return parse_vlm_response(data, page_number, regions)
        except Exception as exc:
            logger.warning("Response parse error (page %d): %s", page_number, exc)
            return None

    def analyze_page(
        self,
        page_image_b64: str,
        regions: list[LayoutRegion],
        page_number: int = 1,
        original_image_b64: Optional[str] = None,
    ) -> Page:
        ocr_context = build_ocr_context(regions)
        prompt_text = PAGE_ANALYSIS_PROMPT.format(ocr_context=ocr_context)

        # Item 1: check for prompt drift
        sent_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:12]
        if settings.log_vlm_io:
            logger.info(
                "Prompt sent to Ollama (page %d): hash=%s | first 400 chars:\n%s",
                page_number, sent_hash, prompt_text[:400],
            )
            if sent_hash.startswith(self._prompt_hash[:6]) is False:
                logger.debug("Note: prompt includes OCR context — hashes will differ (expected).")

        images: list = [page_image_b64]
        figure_count = 0
        for region in regions:
            if (region.image_reference and region.region_type == RegionType.FIGURE
                    and figure_count < 3):
                images.append(region.image_reference)
                figure_count += 1

        logger.info(
            "Sending page %d to Ollama/%s (%d regions, %d images) ...",
            page_number, self._model_name, len(regions), len(images),
        )

        # Item 7: measure model call time
        t0 = time.perf_counter()
        try:
            raw_text = self._call_model(prompt_text, images)
        except Exception as exc:
            logger.error("Ollama call failed for page %d: %s", page_number, exc)
            return make_error_page(page_number, regions, f"Ollama API error: {exc}")
        t_vlm = time.perf_counter() - t0

        # Item 1: log raw response
        if settings.log_vlm_io:
            logger.debug(
                "Ollama raw response (page %d, %.1fs):\n%s",
                page_number, t_vlm, raw_text,
            )
        else:
            logger.debug(
                "Ollama raw response (page %d, %.1fs, first 500):\n%s",
                page_number, t_vlm, raw_text[:500],
            )

        # Item 2: parse with one retry on failure or invalid enum
        page = self._try_parse(raw_text, page_number, regions, strict_enums=True)
        if page is None:
            logger.warning("Parse / enum check failed (page %d) — retrying model call once ...", page_number)
            try:
                raw_text = self._call_model(prompt_text, images)
            except Exception as exc:
                return make_error_page(page_number, regions, f"Ollama retry failed: {exc}")
            page = self._try_parse(raw_text, page_number, regions, strict_enums=False)
            if page is None:
                return make_error_page(
                    page_number, regions,
                    "VLM returned unparseable JSON on both attempts",
                )
            page.warnings.append("Parsed on retry (first attempt failed)")

        # Stash VLM timer for the processor to collect
        page._t_vlm = t_vlm   # type: ignore[attr-defined]

        logger.info(
            "Page %d analysed by Ollama: %d sections, confidence=%s, vlm=%.1fs",
            page_number, len(page.sections), page.confidence, t_vlm,
        )
        return page

    def describe_figure(self, figure_b64: str, context: Optional[str] = None) -> dict:
        prompt = FIGURE_DESCRIPTION_PROMPT.format(context=context or "")
        try:
            raw = self._call_model(prompt, [figure_b64])
            return extract_json(raw)
        except Exception as exc:
            logger.error("Ollama figure description failed: %s", exc)
            return {"description": "Could not describe figure", "confidence": 0.0}

    def provider_name(self) -> str:
        return f"OllamaVLM({self._model_name})"
