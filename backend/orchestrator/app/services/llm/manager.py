"""
File: orchestrator/app/services/llm/manager.py
Description: Central LLM Gateway & Management Service.
             Provides tiered model routing, provider registration, automatic fallback cascading,
             and error isolation.
"""

import os
import logging
from typing import Optional, Dict, Any, List

from app.services.llm.base import BaseLLMProvider, LLMResponse, ModelTier
from app.services.llm.providers.gemini_provider import GeminiProvider
from app.services.llm.providers.openai_provider import OpenAIProvider
from app.services.llm.providers.mock_provider import MockLLMProvider
from app.services.llm.providers.ollama_provider import OllamaProvider
from app.core.config import settings

logger = logging.getLogger("orchestrator.llm.manager")


class LLMManager:
    """
    Central Gateway managing all LLM interactions in the Socratic Orchestrator.
    Decouples core business/pedagogical logic from specific AI vendors.
    """
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self.primary_provider_name: str = getattr(settings, "LLM_PRIMARY_PROVIDER", "gemini").lower()
        self.fallback_provider_name: Optional[str] = getattr(settings, "LLM_FALLBACK_PROVIDER", "ollama")

        self._initialize_default_providers()

    def _initialize_default_providers(self):
        """Initializes default available provider adapters."""
        # 1. Gemini Provider (Primary Cloud)
        try:
            gemini = GeminiProvider()
            self.register_provider("gemini", gemini)
        except Exception as e:
            logger.warning(f"Could not initialize GeminiProvider: {e}")

        # 2. Local Ollama Provider (Local Fallback: llama3.2:3b)
        try:
            ollama = OllamaProvider()
            self.register_provider("ollama", ollama)
        except Exception as e:
            logger.warning(f"Could not initialize OllamaProvider: {e}")

        # 3. OpenAI / Local Compatible Provider
        try:
            openai_p = OpenAIProvider()
            self.register_provider("openai", openai_p)
        except Exception as e:
            logger.warning(f"Could not initialize OpenAIProvider: {e}")

        # 4. Mock Provider for unit testing / offline safety net
        self.register_provider("mock", MockLLMProvider())


    def register_provider(self, name: str, provider: BaseLLMProvider):
        """Registers a provider adapter instance."""
        self._providers[name.lower()] = provider
        logger.info(f"Registered LLM Provider: [{name.lower()}] (available: {provider.is_available()})")

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """Retrieves a registered provider by name."""
        return self._providers.get(name.lower())

    def get_registered_providers(self) -> List[str]:
        return list(self._providers.keys())

    def _get_provider_cascade(self, requested_name: Optional[str] = None) -> List[BaseLLMProvider]:
        """Returns the ordered list of provider candidates to try."""
        primary_name = (requested_name or self.primary_provider_name).lower()
        fallback_name = (self.fallback_provider_name or "ollama").lower()
        
        candidates: List[BaseLLMProvider] = []
        # 1. Primary
        if primary_name in self._providers:
            candidates.append(self._providers[primary_name])
        # 2. Fallback (e.g. Ollama)
        if fallback_name in self._providers and fallback_name != primary_name:
            candidates.append(self._providers[fallback_name])
        # 3. Mock safety net
        if "mock" in self._providers and "mock" not in (primary_name, fallback_name):
            candidates.append(self._providers["mock"])
            
        return candidates

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT,
        provider_name: Optional[str] = None
    ) -> LLMResponse:
        """
        Synchronously generates text using the selected or primary provider,
        cascading to fallback (e.g. Ollama) and mock if errors occur.
        If temperature is None, each provider applies its own configured temperature.
        """
        candidates = self._get_provider_cascade(provider_name)
        if not candidates:
            raise RuntimeError(f"No LLM providers available.")

        last_error = None
        for i, provider in enumerate(candidates):
            if not provider.is_available():
                logger.warning(f"Provider [{provider.name}] is not available. Skipping.")
                continue

            try:
                if i > 0:
                    logger.warning(f"Cascading LLM execution to [{provider.name}].")
                return provider.generate_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_tier=model_tier
                )
            except Exception as e:
                logger.error(f"Provider [{provider.name}] execution error: {e}")
                last_error = e

        if last_error:
            raise last_error
        raise RuntimeError("All candidate LLM providers failed or were unavailable.")

    async def generate_text_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT,
        provider_name: Optional[str] = None
    ) -> LLMResponse:
        """
        Asynchronously generates text with cascading fallback support.
        If temperature is None, each provider applies its own configured temperature.
        """
        candidates = self._get_provider_cascade(provider_name)
        if not candidates:
            raise RuntimeError(f"No LLM providers available.")

        last_error = None
        for i, provider in enumerate(candidates):
            if not provider.is_available():
                logger.warning(f"Provider [{provider.name}] is not available. Skipping.")
                continue

            try:
                if i > 0:
                    logger.warning(f"Cascading async LLM execution to [{provider.name}].")
                return await provider.generate_text_async(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_tier=model_tier
                )
            except Exception as e:
                logger.error(f"Provider [{provider.name}] async execution error: {e}")
                last_error = e

        if last_error:
            raise last_error
        raise RuntimeError("All candidate LLM providers failed or were unavailable.")


class LLMController(LLMManager):
    """
    Central Controller for managing, switching, discovering, and testing LLM providers
    and models at runtime without altering core system code.
    """
    def __init__(self):
        super().__init__()
        self._listeners: List[Any] = []

    def add_listener(self, callback: Any) -> None:
        """Registers a listener callback for LLM configuration change events."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify_listeners(self, event_type: str, data: Dict[str, Any]) -> None:
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.warning(f"Error executing LLM controller listener: {e}")

    def switch_provider(
        self,
        primary_provider: str,
        fallback_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically switches the active primary provider (e.g. 'ollama', 'gemini', 'mock', 'openai')
        and optional fallback provider at runtime.
        """
        target_primary = primary_provider.strip().lower()
        if target_primary not in self._providers:
            raise ValueError(
                f"Unknown LLM provider '{target_primary}'. "
                f"Registered providers: {list(self._providers.keys())}"
            )

        provider_obj = self._providers[target_primary]
        is_avail = provider_obj.is_available()
        if not is_avail:
            logger.warning(f"Switching to provider [{target_primary}], but its current availability is False.")

        old_primary = self.primary_provider_name
        self.primary_provider_name = target_primary

        if fallback_provider is not None:
            target_fallback = fallback_provider.strip().lower()
            if target_fallback in self._providers:
                self.fallback_provider_name = target_fallback
            else:
                logger.warning(f"Unknown fallback provider '{target_fallback}'. Fallback unchanged.")

        logger.info(
            f"Switched Primary LLM Provider: [{old_primary}] -> [{self.primary_provider_name}] "
            f"(Fallback: [{self.fallback_provider_name}], Available: {is_avail})"
        )

        event_data = {
            "old_primary": old_primary,
            "new_primary": self.primary_provider_name,
            "fallback": self.fallback_provider_name,
            "is_available": is_avail,
            "active_model": provider_obj.get_active_model(),
        }
        self._notify_listeners("provider_switched", event_data)

        return {
            "status": "success",
            "message": f"Primary provider switched to '{self.primary_provider_name}'",
            "current_config": self.get_status()
        }

    def switch_model(
        self,
        provider_name: str,
        model_name: str,
        tier: Optional[ModelTier] = None
    ) -> Dict[str, Any]:
        """
        Dynamically switches the model used by a specific provider (e.g. 'qwen3.5:4b' or 'gemma4:e4b' on Ollama).
        Can target a specific ModelTier or all tiers if tier is None.
        """
        pname = provider_name.strip().lower()
        provider = self.get_provider(pname)
        if not provider:
            raise ValueError(
                f"Provider '{pname}' not found. "
                f"Available: {list(self._providers.keys())}"
            )

        clean_model = model_name.strip()
        provider.set_active_model(clean_model, tier=tier)

        tier_str = tier.value if tier else "ALL"
        logger.info(f"Switched Model for Provider [{pname}]: tier={tier_str} -> {clean_model}")

        event_data = {
            "provider": pname,
            "tier": tier_str,
            "new_model": clean_model,
        }
        self._notify_listeners("model_switched", event_data)

        return {
            "status": "success",
            "message": f"Provider '{pname}' model for tier '{tier_str}' set to '{clean_model}'",
            "provider_info": self.get_provider_status(pname)
        }

    def set_provider_endpoint(
        self,
        provider_name: str,
        base_url: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically changes provider base URL (e.g. toggle Ollama local vs remote).
        """
        pname = provider_name.strip().lower()
        provider = self.get_provider(pname)
        if not provider:
            raise ValueError(f"Provider '{pname}' not found.")

        if hasattr(provider, "set_base_url"):
            getattr(provider, "set_base_url")(base_url, api_key=api_key)
            return {
                "status": "success",
                "message": f"Provider '{pname}' endpoint updated to {base_url}",
                "is_available": provider.is_available()
            }
        elif hasattr(provider, "base_url"):
            setattr(provider, "base_url", base_url.rstrip("/"))
            if api_key and hasattr(provider, "api_key"):
                setattr(provider, "api_key", api_key.strip())
            return {
                "status": "success",
                "message": f"Provider '{pname}' endpoint updated to {base_url}",
                "is_available": provider.is_available()
            }
        else:
            raise NotImplementedError(f"Provider '{pname}' does not support custom base URL configuration.")

    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """Returns detailed status of a specific provider."""
        pname = provider_name.strip().lower()
        provider = self.get_provider(pname)
        if not provider:
            return {"name": pname, "registered": False}

        is_avail = provider.is_available()
        models_by_tier = {
            "FAST": provider.get_active_model(ModelTier.FAST),
            "REASONING": provider.get_active_model(ModelTier.REASONING),
            "TRANSLATION": provider.get_active_model(ModelTier.TRANSLATION),
            "DEFAULT": provider.get_active_model(ModelTier.DEFAULT),
        }
        
        info = {
            "name": pname,
            "registered": True,
            "available": is_avail,
            "active_model": provider.get_active_model(),
            "models_by_tier": models_by_tier,
            "is_primary": (pname == self.primary_provider_name),
            "is_fallback": (pname == self.fallback_provider_name),
        }

        # Include base_url if applicable (e.g. Ollama, OpenAI)
        if hasattr(provider, "base_url"):
            info["base_url"] = getattr(provider, "base_url")

        return info

    def get_status(self) -> Dict[str, Any]:
        """
        Returns full diagnostic status of the LLM Controller:
        active primary, fallback, and status of every registered provider.
        """
        import time
        providers_status = {}
        for pname in self._providers:
            providers_status[pname] = self.get_provider_status(pname)

        primary_obj = self.get_provider(self.primary_provider_name)
        active_model = primary_obj.get_active_model() if primary_obj else "unknown"

        return {
            "primary_provider": self.primary_provider_name,
            "fallback_provider": self.fallback_provider_name,
            "active_model": active_model,
            "registered_providers": list(self._providers.keys()),
            "providers": providers_status,
            "timestamp": time.time(),
        }

    def list_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discovers and catalogs all available models across all registered providers
        (including live querying of local Ollama /api/tags).
        """
        catalog: Dict[str, List[Dict[str, Any]]] = {}
        for pname, provider in self._providers.items():
            try:
                models = provider.list_available_models()
                catalog[pname] = models
            except Exception as e:
                logger.debug(f"Failed to list models for provider [{pname}]: {e}")
                catalog[pname] = [{"name": provider.get_active_model(), "provider": pname}]
        return catalog

    def test_generation(
        self,
        prompt: str = "Hello! Please reply with 'SYSTEM READY' in 2 words.",
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> Dict[str, Any]:
        """
        Performs an isolated generation test against a target provider and model
        without permanently modifying current routing settings.
        """
        import time
        target_name = (provider_name or self.primary_provider_name).strip().lower()
        provider = self.get_provider(target_name)
        if not provider:
            return {
                "success": False,
                "error": f"Provider '{target_name}' is not registered.",
                "provider": target_name
            }

        if not provider.is_available():
            return {
                "success": False,
                "error": f"Provider '{target_name}' is not currently available/reachable.",
                "provider": target_name
            }

        # Save previous model if temporary override requested
        original_model = provider.get_active_model(model_tier)
        try:
            if model_name:
                provider.set_active_model(model_name, tier=model_tier)

            start = time.time()
            resp = provider.generate_text(
                prompt=prompt,
                model_tier=model_tier,
                max_tokens=64
            )
            elapsed_ms = (time.time() - start) * 1000.0

            return {
                "success": True,
                "provider": resp.provider,
                "model_name": resp.model_name,
                "response_text": resp.text,
                "latency_ms": round(elapsed_ms, 2),
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
            }
        except Exception as e:
            return {
                "success": False,
                "provider": target_name,
                "error": str(e),
            }
        finally:
            if model_name and hasattr(provider, "set_active_model"):
                provider.set_active_model(original_model, tier=model_tier)


# Global Singleton Gateway & Controller
llm_service = LLMController()
