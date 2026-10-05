"""
File: orchestrator/app/services/llm/providers/openai_provider.py
Description: Provider adapter for OpenAI API and OpenAI-compatible endpoints
             (Ollama, vLLM, DeepSeek, LocalAI).
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.services.llm.base import BaseLLMProvider, LLMResponse, ModelTier
from app.core.config import settings

logger = logging.getLogger("orchestrator.llm.openai")


class OpenAIProvider(BaseLLMProvider):
    """
    Adapter for OpenAI and OpenAI-compatible chat completions API (/v1/chat/completions).
    Uses standard httpx client for zero extra dependencies.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        fast_model: str = "gpt-4o-mini",
        reasoning_model: str = "gpt-4o",
        translation_model: str = "gpt-4o-mini",
        temperature: Optional[float] = None,
        timeout: float = 30.0
    ):
        configured_temp = temperature if temperature is not None else getattr(settings, "OPENAI_TEMPERATURE", 0.7)
        super().__init__(name="openai", default_temperature=configured_temp)
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.fast_model_name = fast_model
        self.reasoning_model_name = reasoning_model
        self.translation_model_name = translation_model
        self.timeout = timeout

    def is_available(self) -> bool:
        # Local servers (e.g. Ollama or vLLM) may not require an API key
        is_local = "localhost" in self.base_url or "127.0.0.1" in self.base_url
        return bool(self.api_key or is_local)

    def _resolve_model_name(self, tier: ModelTier) -> str:
        if tier == ModelTier.FAST:
            return self.fast_model_name
        elif tier == ModelTier.REASONING:
            return self.reasoning_model_name
        elif tier == ModelTier.TRANSLATION:
            return self.translation_model_name
        return self.fast_model_name

    def _build_payload(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        model_name: str
    ) -> Dict[str, Any]:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("OpenAIProvider is not configured with an API key or accessible base URL.")

        eff_temp = self.default_temperature if temperature is None else temperature
        model_name = self._resolve_model_name(model_tier)
        payload = self._build_payload(prompt, system_instruction, eff_temp, max_tokens, model_name)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'none'}"
        }

        start_time = time.time()
        url = f"{self.base_url}/chat/completions"

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.time() - start_time) * 1000

        choices = data.get("choices", [])
        text = choices[0].get("message", {}).get("content", "").strip() if choices else ""
        usage = data.get("usage", {})

        return LLMResponse(
            text=text,
            provider="openai",
            model_name=model_name,
            prompt_tokens=usage.get("prompt_tokens", len(prompt.split())),
            completion_tokens=usage.get("completion_tokens", len(text.split())),
            total_tokens=usage.get("total_tokens", len(prompt.split()) + len(text.split())),
            latency_ms=round(latency_ms, 2),
            raw_metadata={"tier": model_tier.value, "temperature": eff_temp}
        )

    async def generate_text_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("OpenAIProvider is not configured with an API key or accessible base URL.")

        eff_temp = self.default_temperature if temperature is None else temperature
        model_name = self._resolve_model_name(model_tier)
        payload = self._build_payload(prompt, system_instruction, eff_temp, max_tokens, model_name)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'none'}"
        }

        start_time = time.time()
        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.time() - start_time) * 1000

        choices = data.get("choices", [])
        text = choices[0].get("message", {}).get("content", "").strip() if choices else ""
        usage = data.get("usage", {})

        return LLMResponse(
            text=text,
            provider="openai",
            model_name=model_name,
            prompt_tokens=usage.get("prompt_tokens", len(prompt.split())),
            completion_tokens=usage.get("completion_tokens", len(text.split())),
            total_tokens=usage.get("total_tokens", len(prompt.split()) + len(text.split())),
            latency_ms=round(latency_ms, 2),
            raw_metadata={"tier": model_tier.value}
        )

    def get_active_model(self, tier: ModelTier = ModelTier.DEFAULT) -> str:
        return self._resolve_model_name(tier)

    def set_active_model(self, model_name: str, tier: Optional[ModelTier] = None) -> None:
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
        return [
            {"name": "gpt-4o-mini", "provider": "openai", "tier": "fast", "description": "High-efficiency, low latency reasoning"},
            {"name": "gpt-4o", "provider": "openai", "tier": "reasoning", "description": "Flagship multimodal intelligence"},
            {"name": "gpt-3.5-turbo", "provider": "openai", "tier": "legacy", "description": "Standard fast text model"},
        ]
