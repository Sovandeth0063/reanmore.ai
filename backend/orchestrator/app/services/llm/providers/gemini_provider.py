"""
File: orchestrator/app/services/llm/providers/gemini_provider.py
Description: Modern Google Gemini Adapter implementing BaseLLMProvider via google.genai SDK.
"""

import os
import time
import logging
import asyncio
from typing import Optional, Dict, Any, List

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

from app.services.llm.base import BaseLLMProvider, LLMResponse, ModelTier
from app.core.config import settings

logger = logging.getLogger("orchestrator.llm.gemini")

# Order: gemini-3.5-flash first as primary, followed by 3.6-flash, 2.0-flash, and 1.5-flash
CANDIDATE_MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-2.0-flash", "gemini-1.5-flash"]


class GeminiProvider(BaseLLMProvider):
    """
    Adapter for Google Gemini API via official google.genai SDK.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        fast_model: Optional[str] = None,
        reasoning_model: Optional[str] = None,
        translation_model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 1
    ):
        configured_temp = temperature if temperature is not None else getattr(settings, "GEMINI_TEMPERATURE", 0.7)
        super().__init__(name="gemini", default_temperature=configured_temp)
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")

        default_model = getattr(settings, "GEMINI_MODEL", "") or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        self.fast_model_name = fast_model or default_model
        self.reasoning_model_name = reasoning_model or default_model
        self.translation_model_name = translation_model or default_model
        self.max_retries = max_retries
        self._client: Optional[Any] = None

        if GENAI_AVAILABLE and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google.genai Client: {e}")

    def is_available(self) -> bool:
        return bool(GENAI_AVAILABLE and self._client is not None and self.api_key)

    def _resolve_candidate_models(self, tier: ModelTier) -> List[str]:
        primary = self.fast_model_name
        if tier == ModelTier.REASONING:
            primary = self.reasoning_model_name
        elif tier == ModelTier.TRANSLATION:
            primary = self.translation_model_name

        # Ensure priority model comes first, followed by alternates
        models = [primary]
        for c in CANDIDATE_MODELS:
            if c not in models:
                models.append(c)
        return models

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        if not self.is_available() or not self._client:
            raise RuntimeError("GeminiProvider is not configured with a valid API key.")

        eff_temp = self.default_temperature if temperature is None else temperature
        candidate_models = self._resolve_candidate_models(model_tier)
        start_time = time.time()

        config = types.GenerateContentConfig(
            temperature=eff_temp,
            system_instruction=system_instruction,
            max_output_tokens=max_tokens,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        last_exc = None
        for model_name in candidate_models:
            for attempt in range(1, self.max_retries + 2):
                try:
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )
                    latency_ms = (time.time() - start_time) * 1000
                    text = response.text.strip() if response and response.text else ""

                    usage = getattr(response, "usage_metadata", None)
                    prompt_tokens = getattr(usage, "prompt_token_count", len(prompt.split())) if usage else len(prompt.split())
                    completion_tokens = getattr(usage, "candidates_token_count", len(text.split())) if usage else len(text.split())

                    return LLMResponse(
                        text=text,
                        provider="gemini",
                        model_name=model_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                        latency_ms=round(latency_ms, 2),
                        raw_metadata={"tier": model_tier.value, "temperature": eff_temp}
                    )
                except Exception as exc:
                    last_exc = exc
                    exc_str = str(exc).lower()
                    logger.warning(f"Gemini model {model_name} attempt {attempt} failed ({exc})")

                    # If quota exhausted (429) or model not found (404), immediately switch to next model
                    if "429" in exc_str or "resource_exhausted" in exc_str or "quota" in exc_str or "404" in exc_str:
                        break

                    if attempt <= self.max_retries:
                        time.sleep(0.5 * attempt)
                    else:
                        break

        raise last_exc or RuntimeError("All candidate Gemini models failed.")

    async def generate_text_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        # Run blocking SDK call in default executor thread to avoid blocking asyncio event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                max_tokens=max_tokens,
                model_tier=model_tier,
            )
        )

    def get_active_model(self, tier: ModelTier = ModelTier.DEFAULT) -> str:
        """Returns active Gemini model name for the specified tier."""
        if tier == ModelTier.REASONING:
            return self.reasoning_model_name
        elif tier == ModelTier.TRANSLATION:
            return self.translation_model_name
        return self.fast_model_name

    def set_active_model(self, model_name: str, tier: Optional[ModelTier] = None) -> None:
        """Dynamically updates active Gemini model for a tier or globally."""
        if tier == ModelTier.FAST:
            self.fast_model_name = model_name
        elif tier == ModelTier.REASONING:
            self.reasoning_model_name = model_name
        elif tier == ModelTier.TRANSLATION:
            self.translation_model_name = model_name
        else:
            self.fast_model_name = model_name
            self.reasoning_model_name = model_name
            self.translation_model_name = model_name

    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Queries Google GenAI API or returns structured catalog of Gemini models
        matching the exact metadata schema of local LLM models (name, provider, size_mb,
        parameter_size, quantization_level, family, capabilities, context_length, description).
        """
        now = time.time()
        if hasattr(self, "_cached_models") and (now - getattr(self, "_last_models_check", 0.0) < 60.0):
            return self._cached_models

        discovered: List[Dict[str, Any]] = []

        # 1. Dynamic API Discovery via google.genai SDK if online
        if self.is_available() and self._client:
            try:
                models_pager = self._client.models.list()
                for m in models_pager:
                    m_name = getattr(m, "name", "")
                    clean_name = m_name.replace("models/", "")
                    if "gemini" not in clean_name.lower():
                        continue
                    display_name = getattr(m, "display_name", clean_name)
                    input_limit = getattr(m, "input_token_limit", 1048576)
                    discovered.append({
                        "name": clean_name,
                        "provider": "gemini",
                        "size_mb": 0.0,
                        "parameter_size": "Cloud",
                        "quantization_level": "Server-side",
                        "family": "gemini",
                        "context_length": input_limit,
                        "capabilities": ["completion", "vision", "chat", "multimodal"],
                        "tier": "reasoning" if "pro" in clean_name else "fast",
                        "description": getattr(m, "description", f"Google Cloud: {display_name}") or f"Google Cloud: {display_name}",
                    })
            except Exception as e:
                logger.debug(f"Dynamic Gemini model discovery via API failed: {e}")

        if discovered:
            self._cached_models = discovered
            self._last_models_check = now
            return discovered

        # 2. Curated standard catalog formatted matching local LLM schema
        catalog = [
            {
                "name": "gemini-3.6-flash",
                "provider": "gemini",
                "size_mb": 0.0,
                "parameter_size": "Flash (High Quota)",
                "quantization_level": "Cloud FP16",
                "family": "gemini",
                "context_length": 1048576,
                "capabilities": ["completion", "vision", "chat", "multimodal", "thinking"],
                "tier": "fast_and_reasoning",
                "description": "High quota, ultra-low latency multimodal flash tier (Default Production)",
            },
            {
                "name": "gemini-3.5-flash",
                "provider": "gemini",
                "size_mb": 0.0,
                "parameter_size": "Flash",
                "quantization_level": "Cloud FP16",
                "family": "gemini",
                "context_length": 1048576,
                "capabilities": ["completion", "vision", "chat", "multimodal"],
                "tier": "fast",
                "description": "Stable production multimodal flash model",
            },
            {
                "name": "gemini-2.0-flash",
                "provider": "gemini",
                "size_mb": 0.0,
                "parameter_size": "Next-Gen Flash",
                "quantization_level": "Cloud FP16",
                "family": "gemini",
                "context_length": 1048576,
                "capabilities": ["completion", "vision", "chat", "multimodal", "thinking"],
                "tier": "fast",
                "description": "Next-generation fast multimodal reasoning model",
            },
            {
                "name": "gemini-1.5-flash",
                "provider": "gemini",
                "size_mb": 0.0,
                "parameter_size": "Flash",
                "quantization_level": "Cloud FP16",
                "family": "gemini",
                "context_length": 1048576,
                "capabilities": ["completion", "vision", "chat", "multimodal"],
                "tier": "fast",
                "description": "High-efficiency, lightweight multimodal model",
            },
            {
                "name": "gemini-flash-lite-latest",
                "provider": "gemini",
                "size_mb": 0.0,
                "parameter_size": "Lite",
                "quantization_level": "Cloud FP16",
                "family": "gemini",
                "context_length": 1048576,
                "capabilities": ["completion", "vision", "chat"],
                "tier": "fast",
                "description": "Lightweight, fastest token generation",
            },
            {
                "name": "gemini-1.5-pro",
                "provider": "gemini",
                "size_mb": 0.0,
                "parameter_size": "Pro",
                "quantization_level": "Cloud FP16",
                "family": "gemini",
                "context_length": 2097152,
                "capabilities": ["completion", "vision", "chat", "multimodal", "reasoning"],
                "tier": "reasoning",
                "description": "Deep reasoning & extended 2M token mathematical context",
            },
        ]
        self._cached_models = catalog
        self._last_models_check = now
        return catalog
