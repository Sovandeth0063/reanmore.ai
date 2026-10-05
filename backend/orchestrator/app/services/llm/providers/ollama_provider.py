"""
File: orchestrator/app/services/llm/providers/ollama_provider.py
Description: Local and Cloud Ollama Provider adapter implementing BaseLLMProvider.
             Enables zero-cost, private, offline LLM inference via local Ollama models (e.g. qwen3.5:4b, gemma4:e4b, llama3.2:3b),
             or remote/cloud Ollama endpoints.
"""

import os
import re
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
import httpx

from app.services.llm.base import BaseLLMProvider, LLMResponse, ModelTier
from app.core.config import settings

logger = logging.getLogger("orchestrator.llm.ollama")


def _clean_thinking_tokens(text: str) -> Tuple[str, Optional[str]]:
    """
    Strips internal thinking/reasoning blocks (e.g. Qwen 3.5 or DeepSeek thinking tags)
    from LLM outputs to preserve clean pedagogical dialog for elementary students.
    Returns (cleaned_text, extracted_thinking).
    """
    thinking = None
    if "<think>" in text and "</think>" in text:
        parts = text.split("</think>", 1)
        thinking = parts[0].replace("<think>", "").strip()
        text = parts[1].strip()
    elif "Thinking Process:" in text:
        match = re.search(r"Thinking Process:.*?\n\n(.*)", text, re.DOTALL)
        if match:
            thinking = text[:match.start(1)].strip()
            text = match.group(1).strip()
    return text, thinking


class OllamaProvider(BaseLLMProvider):
    """
    Adapter for local and remote Ollama instances.
    Supports dynamic model switching, automatic model discovery via /api/tags,
    and fallback resolution to installed models.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: str = "qwen3.5:4b",
        fast_model: str = "qwen3.5:4b",
        reasoning_model: str = "gemma4:e4b",
        translation_model: str = "qwen3.5:4b",
        temperature: Optional[float] = None,
        timeout: float = 60.0
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
        self._cached_models: List[Dict[str, Any]] = []
        self._last_models_check: float = 0.0

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def set_base_url(self, base_url: str, api_key: Optional[str] = None) -> None:
        """Dynamically updates the Ollama base URL (e.g. toggling local localhost:11434 vs remote)."""
        self.base_url = base_url.rstrip("/")
        if api_key is not None:
            self.api_key = api_key.strip()
        # Invalidate availability and model cache
        if hasattr(self, "_is_avail_cached"):
            delattr(self, "_is_avail_cached")
        self._cached_models = []
        self._last_models_check = 0.0
        logger.info(f"Ollama base URL switched to [{self.base_url}]")

    def is_available(self) -> bool:
        """Checks if Ollama daemon is reachable with 30-second caching."""
        now = time.time()
        if hasattr(self, "_last_avail_check") and (now - self._last_avail_check < 30.0):
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

    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Queries Ollama /api/tags to list installed models with parameters, size, and capabilities.
        """
        now = time.time()
        if self._cached_models and (now - self._last_models_check < 15.0):
            return self._cached_models

        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.base_url}/api/tags", headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    raw_models = data.get("models", [])
                    parsed = []
                    for m in raw_models:
                        name = m.get("name") or m.get("model", "")
                        details = m.get("details", {})
                        size_mb = round(m.get("size", 0) / (1024 * 1024), 1)
                        param_size = details.get("parameter_size", "")
                        quant = details.get("quantization_level", "")
                        parsed.append({
                            "name": name,
                            "provider": "ollama",
                            "size_mb": size_mb,
                            "parameter_size": param_size,
                            "quantization_level": quant,
                            "family": details.get("family", ""),
                            "capabilities": m.get("capabilities", []),
                            "description": f"Ollama {name} ({param_size}, {quant})"
                        })
                    self._cached_models = parsed
                    self._last_models_check = now
                    return parsed
        except Exception as e:
            logger.debug(f"Could not fetch Ollama models from {self.base_url}: {e}")

        return self._cached_models

    def _resolve_model_name(self, tier: ModelTier) -> str:
        if tier == ModelTier.FAST:
            candidate = self.fast_model_name
        elif tier == ModelTier.REASONING:
            candidate = self.reasoning_model_name
        elif tier == ModelTier.TRANSLATION:
            candidate = self.translation_model_name
        else:
            candidate = self.default_model

        # If candidate is the default unconfigured placeholder ('llama3.2:3b'), auto-select first installed model
        try:
            if candidate in ("llama3.2:3b", ""):
                installed = self.list_available_models()
                if installed:
                    installed_names = [m["name"] for m in installed]
                    if candidate not in installed_names:
                        logger.info(
                            f"Ollama default model '{candidate}' not found in installed models {installed_names}. "
                            f"Auto-falling back to '{installed_names[0]}'."
                        )
                        return installed_names[0]
        except Exception as e:
            logger.debug(f"Model resolution auto-fallback check failed: {e}")

        return candidate

    def get_active_model(self, tier: ModelTier = ModelTier.DEFAULT) -> str:
        """Returns the active model resolved for the given tier."""
        return self._resolve_model_name(tier)

    def set_active_model(self, model_name: str, tier: Optional[ModelTier] = None) -> None:
        """Dynamically updates the active model for a specific tier or globally."""
        if tier == ModelTier.FAST:
            self.fast_model_name = model_name
        elif tier == ModelTier.REASONING:
            self.reasoning_model_name = model_name
        elif tier == ModelTier.TRANSLATION:
            self.translation_model_name = model_name
        else:
            self.default_model = model_name
            self.fast_model_name = model_name
            self.reasoning_model_name = model_name
            self.translation_model_name = model_name
        logger.info(f"Ollama active model updated: tier={tier} -> {model_name}")

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
            raw_text = data.get("message", {}).get("content", "")
            thinking_field = data.get("message", {}).get("thinking", "")
            clean_text, thinking = _clean_thinking_tokens(raw_text)
            if not clean_text and thinking_field:
                clean_text = thinking_field.strip()
                thinking = thinking_field

            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            raw_meta = {"temperature": eff_temp, **data}
            if thinking:
                raw_meta["thinking"] = thinking

            return LLMResponse(
                text=clean_text,
                provider="ollama",
                model_name=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2),
                raw_metadata=raw_meta
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
            raw_text = data.get("message", {}).get("content", "")
            thinking_field = data.get("message", {}).get("thinking", "")
            clean_text, thinking = _clean_thinking_tokens(raw_text)
            if not clean_text and thinking_field:
                clean_text = thinking_field.strip()
                thinking = thinking_field

            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            raw_meta = {"temperature": eff_temp, **data}
            if thinking:
                raw_meta["thinking"] = thinking

            return LLMResponse(
                text=clean_text,
                provider="ollama",
                model_name=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2),
                raw_metadata=raw_meta
            )
        except Exception as e:
            logger.error(f"Ollama async text generation failed on {model}: {e}")
            raise RuntimeError(f"Ollama async generation error: {e}") from e

    def get_info(self) -> Dict[str, Any]:
        """Returns runtime diagnostic information about Ollama provider."""
        return {
            "name": self.name,
            "available": self.is_available(),
            "base_url": self.base_url,
            "default_temperature": self.default_temperature,
            "active_model": self.get_active_model(),
            "models_by_tier": {
                "FAST": self.get_active_model(ModelTier.FAST),
                "REASONING": self.get_active_model(ModelTier.REASONING),
                "TRANSLATION": self.get_active_model(ModelTier.TRANSLATION),
                "DEFAULT": self.get_active_model(ModelTier.DEFAULT),
            },
            "installed_models": self.list_available_models(),
        }
