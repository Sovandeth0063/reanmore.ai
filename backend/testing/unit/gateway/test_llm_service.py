"""
File: testing/test_llm_service.py
Description: Comprehensive Unit and Integration Test Suite for the LLM Management Service.
             Tests:
             1. BaseLLMProvider and LLMResponse schema contract.
             2. MockLLMProvider generation and latency metrics.
             3. LLMManager provider registration, lookup, and tier routing.
             4. Automatic fallback cascading when primary provider fails.
             5. Decoupled provider swapping (switching providers with zero core code refactoring).
"""

import os
import sys
# pyrefly: ignore [missing-import]
import pytest

# Ensure repo root and orchestrator are on sys.path
def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator")))

# pyrefly: ignore [missing-import]
from app.services.llm.base import BaseLLMProvider, LLMResponse, ModelTier
# pyrefly: ignore [missing-import]
from app.services.llm.manager import LLMManager, llm_service
# pyrefly: ignore [missing-import]
from app.services.llm.providers.mock_provider import MockLLMProvider
# pyrefly: ignore [missing-import]
from app.services.llm.providers.gemini_provider import GeminiProvider
# pyrefly: ignore [missing-import]
from app.services.llm.providers.openai_provider import OpenAIProvider
# pyrefly: ignore [missing-import]
from app.services.llm.providers.ollama_provider import OllamaProvider
# pyrefly: ignore [missing-import]
from app.core.config import settings



def test_mock_provider_generation():
    provider = MockLLMProvider(default_response="The answer is 42.")
    assert provider.is_available() is True

    resp = provider.generate_text(
        prompt="What is the meaning of life?",
        system_instruction="Be concise.",
        model_tier=ModelTier.FAST
    )
    assert isinstance(resp, LLMResponse)
    assert resp.text == "The answer is 42."
    assert resp.provider == "mock"
    assert resp.model_name == "mock-fast"
    assert resp.prompt_tokens > 0
    assert resp.completion_tokens > 0
    assert resp.latency_ms >= 0.0


@pytest.mark.asyncio
async def test_mock_provider_async_generation():
    provider = MockLLMProvider(default_response="Async result")
    resp = await provider.generate_text_async(
        prompt="Solve 10 - 4",
        model_tier=ModelTier.REASONING
    )
    assert resp.text == "Async result"
    assert resp.model_name == "mock-reasoning"


def test_llm_manager_registration():
    mgr = LLMManager()
    custom_mock = MockLLMProvider(default_response="Custom mock")
    mgr.register_provider("custom_test", custom_mock)

    assert "custom_test" in mgr.get_registered_providers()
    assert mgr.get_provider("custom_test") is custom_mock

    resp = mgr.generate_text("Hello", provider_name="custom_test")
    assert resp.text == "Custom mock"


def test_llm_manager_model_tiers():
    mgr = LLMManager()
    mock_p = MockLLMProvider(response_handler=lambda p: f"Processed: {p}")
    mgr.register_provider("test_tier", mock_p)

    resp_fast = mgr.generate_text("query 1", model_tier=ModelTier.FAST, provider_name="test_tier")
    assert resp_fast.model_name == "mock-fast"

    resp_reasoning = mgr.generate_text("query 2", model_tier=ModelTier.REASONING, provider_name="test_tier")
    assert resp_reasoning.model_name == "mock-reasoning"

    resp_trans = mgr.generate_text("query 3", model_tier=ModelTier.TRANSLATION, provider_name="test_tier")
    assert resp_trans.model_name == "mock-translation"


def test_llm_manager_automatic_fallback_on_unavailable():
    mgr = LLMManager()
    # Primary provider that is unavailable
    primary = MockLLMProvider(should_fail=True)
    # Fallback provider that works
    fallback = MockLLMProvider(default_response="Fallback succeeded!")

    mgr.register_provider("failing_primary", primary)
    mgr.register_provider("working_fallback", fallback)

    mgr.primary_provider_name = "failing_primary"
    mgr.fallback_provider_name = "working_fallback"

    # Primary is unavailable (is_available=False because should_fail=True)
    resp = mgr.generate_text("Test prompt")
    assert resp.text == "Fallback succeeded!"
    assert resp.provider == "mock"


def test_llm_manager_automatic_fallback_on_runtime_error():
    mgr = LLMManager()
    
    class CrashingProvider(BaseLLMProvider):
        def __init__(self):
            super().__init__(name="crashing")
        def is_available(self):
            return True
        def generate_text(self, *args, **kwargs):
            raise ConnectionError("Quota exceeded or simulated 429")
        async def generate_text_async(self, *args, **kwargs):
            raise ConnectionError("Quota exceeded or simulated 429")

    crashing_primary = CrashingProvider()
    working_fallback = MockLLMProvider(default_response="Recovered via fallback!")

    mgr.register_provider("crashing_primary", crashing_primary)
    mgr.register_provider("working_fallback", working_fallback)

    mgr.primary_provider_name = "crashing_primary"
    mgr.fallback_provider_name = "working_fallback"

    # Should catch ConnectionError and seamlessly return from fallback
    resp = mgr.generate_text("Explain fractions")
    assert resp.text == "Recovered via fallback!"


def test_provider_swap_without_code_change():
    """
    Demonstrates switching from Gemini to a different provider
    without modifying core tutor code.
    """
    original_primary = llm_service.primary_provider_name
    try:
        # Create a new custom mock provider (e.g. simulating local Ollama Llama-3)
        llama3_mock = MockLLMProvider(default_response="Simulated Llama-3 8B response")
        llm_service.register_provider("llama3", llama3_mock)

        # Switch primary provider
        llm_service.primary_provider_name = "llama3"

        resp = llm_service.generate_text("What is water?")
        assert resp.text == "Simulated Llama-3 8B response"
        assert resp.provider == "mock"  # from MockLLMProvider
    finally:
        llm_service.primary_provider_name = original_primary


def test_ollama_provider_integration():
    ollama_p = OllamaProvider()
    assert ollama_p.name == "ollama"
    assert ollama_p.default_model == settings.OLLAMA_MODEL

    # If local Ollama is available, test live generation; otherwise verify schema/availability
    if ollama_p.is_available():
        resp = ollama_p.generate_text("Say 1+1=2", max_tokens=10)
        assert isinstance(resp, LLMResponse)
        assert resp.provider == "ollama"
        assert resp.model_name == ollama_p.default_model
        assert len(resp.text) > 0


def test_llm_manager_defaults_gemini_primary_ollama_fallback():
    mgr = LLMManager()
    assert mgr.primary_provider_name == settings.LLM_PRIMARY_PROVIDER.lower()
    assert mgr.fallback_provider_name == settings.LLM_FALLBACK_PROVIDER
    assert "ollama" in mgr.get_registered_providers()
    assert "gemini" in mgr.get_registered_providers()


def test_provider_specific_temperature_configuration():
    mgr = LLMManager()
    gemini = mgr.get_provider("gemini")
    ollama = mgr.get_provider("ollama")

    assert gemini.default_temperature == 0.7
    assert ollama.default_temperature == settings.OLLAMA_TEMPERATURE

    # Verify custom mock provider with custom default temperature
    mock_creative = MockLLMProvider(default_temperature=0.9)
    assert mock_creative.default_temperature == 0.9

    # Without explicit temperature, provider uses its own default temperature
    resp = mock_creative.generate_text("Generate a story")
    assert resp.raw_metadata["temperature"] == 0.9

    # With explicit temperature, caller override takes precedence
    resp_override = mock_creative.generate_text("Generate code", temperature=0.1)
    assert resp_override.raw_metadata["temperature"] == 0.1


