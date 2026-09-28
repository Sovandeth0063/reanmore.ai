"""
File: orchestrator/app/services/llm/providers/ollama_provider.py
Description: Local Ollama Provider adapter implementing BaseLLMProvider.
             Enables zero-cost, private, offline LLM inference via local Ollama models (e.g. llama3.2:3b).
"""

import os
import time
import logging
from typing import Optional, Dict, Any
import httpx

from app.services.llm.base import BaseLLMProvider, LLMResponse, ModelTier
from app.core.config import settings

logger = logging.getLogger("orchestrator.llm.ollama")


class OllamaProvider(BaseLLMProvider):
    """
    Adapter for local Ollama instances running on http://localhost:11434.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: str = "llama3.2:3b",
        fast_model: str = "llama3.2:3b",
        reasoning_model: str = "llama3.2:3b",
        translation_model: str = "llama3.2:3b",
        temperature: Optional[float] = None,
        timeout: float = 45.0
    ):
        configured_temp = temperature if temperature is not None else getattr(settings, "OLLAMA_TEMPERATURE", 0.2)
        super().__init__(name="ollama", default_temperature=configured_temp)
        configured_url = getattr(settings, "OLLAMA_BASE_URL", "") or os.getenv("OLLAMA_BASE_URL", "")
        self.base_url = (base_url or configured_url or "http://localhost:11434").rstrip("/")
        
        configured_api_key = getattr(settings, "OLLAMA_API_KEY", "") or os.getenv("OLLAMA_API_KEY", "")
        self.api_key = configured_api_key.strip() if configured_api_key else ""

        configured_model = getattr(settings, "OLLAMA_MODEL", "") or os.getenv("OLLAMA_MODEL", "")
        self.default_model = configured_model or default_model
        self.fast_model_name = getattr(settings, "OLLAMA_FAST_MODEL", "") or fast_model or self.default_model
        self.reasoning_model_name = getattr(settings, "OLLAMA_REASONING_MODEL", "") or reasoning_model or self.default_model
        self.translation_model_name = getattr(settings, "OLLAMA_TRANSLATION_MODEL", "") or translation_model or self.default_model
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_available(self) -> bool:
        """Checks if local or remote Ollama daemon is reachable with 60-second caching."""
        now = time.time()
        if hasattr(self, "_last_avail_check") and (now - self._last_avail_check < 60.0):
            return getattr(self, "_is_avail_cached", False)
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags", headers=self._get_headers())
                self._is_avail_cached = (res.status_code == 200)
                self._last_avail_check = now
                return self._is_avail_cached
        except Exception:
            self._is_avail_cached = False
            self._last_avail_check = now
            return False

    def _resolve_model_name(self, tier: ModelTier) -> str:
        if tier == ModelTier.FAST:
            return self.fast_model_name
        elif tier == ModelTier.REASONING:
            return self.reasoning_model_name
        elif tier == ModelTier.TRANSLATION:
            return self.translation_model_name
        return self.default_model

    def _build_messages(self, prompt: str, system_instruction: Optional[str]) -> list:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        eff_temp = self.default_temperature if temperature is None else temperature
        model = self._resolve_model_name(model_tier)
        messages = self._build_messages(prompt, system_instruction)
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": eff_temp
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        start_time = time.time()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            latency_ms = (time.time() - start_time) * 1000.0
            generated_text = data.get("message", {}).get("content", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return LLMResponse(
                text=generated_text,
                provider="ollama",
                model_name=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2),
                raw_metadata={"temperature": eff_temp, **data}
            )
        except Exception as e:
            logger.error(f"Ollama text generation failed on {model}: {e}")
            raise RuntimeError(f"Ollama generation error: {e}") from e

    async def generate_text_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        eff_temp = self.default_temperature if temperature is None else temperature
        model = self._resolve_model_name(model_tier)
        messages = self._build_messages(prompt, system_instruction)
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": eff_temp
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            latency_ms = (time.time() - start_time) * 1000.0
            generated_text = data.get("message", {}).get("content", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return LLMResponse(
                text=generated_text,
                provider="ollama",
                model_name=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2),
                raw_metadata=data
            )
        except Exception as e:
            logger.error(f"Ollama async text generation failed on {model}: {e}")
            raise RuntimeError(f"Ollama async generation error: {e}") from e
