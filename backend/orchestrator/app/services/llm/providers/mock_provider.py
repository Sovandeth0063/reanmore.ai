"""
File: orchestrator/app/services/llm/providers/mock_provider.py
Description: Predictable, zero-cost, zero-latency Mock LLM Provider for unit testing,
             offline development, and CI/CD pipelines.
"""

import time
from typing import Optional, Dict, Any, Callable
from app.services.llm.base import BaseLLMProvider, LLMResponse, ModelTier


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM Provider that returns predefined responses or echoes responses.
    Allows testing error handling, fallback chains, and state machine transitions offline.
    """
    def __init__(
        self,
        default_response: str = "Mock LLM generated response.",
        response_handler: Optional[Callable[[str], str]] = None,
        should_fail: bool = False,
        failure_exception: Optional[Exception] = None,
        default_temperature: float = 0.7
    ):
        super().__init__(name="mock", default_temperature=default_temperature)
        self.default_response = default_response
        self.response_handler = response_handler
        self.should_fail = should_fail
        self.failure_exception = failure_exception or RuntimeError("Simulated Mock LLM failure")
        self.call_history = []

    def is_available(self) -> bool:
        return not self.should_fail

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        eff_temp = self.default_temperature if temperature is None else temperature
        start_time = time.time()
        self.call_history.append({
            "prompt": prompt,
            "system_instruction": system_instruction,
            "temperature": eff_temp,
            "model_tier": model_tier
        })

        if self.should_fail:
            raise self.failure_exception

        if self.response_handler:
            text = self.response_handler(prompt)
        else:
            text = self.default_response

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            text=text,
            provider="mock",
            model_name=f"mock-{model_tier.value.lower()}",
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(text.split()),
            total_tokens=len(prompt.split()) + len(text.split()),
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
        return self.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            model_tier=model_tier
        )

    def get_active_model(self, tier: ModelTier = ModelTier.DEFAULT) -> str:
        return f"mock-{tier.value.lower()}"

    def set_active_model(self, model_name: str, tier: Optional[ModelTier] = None) -> None:
        self.default_model = model_name

    def list_available_models(self) -> list:
        return [
            {"name": "mock-fast", "provider": "mock", "tier": "fast", "description": "Predictable instant mock for unit tests"},
            {"name": "mock-reasoning", "provider": "mock", "tier": "reasoning", "description": "Predictable Socratic reasoning mock"},
            {"name": "mock-translation", "provider": "mock", "tier": "translation", "description": "Predictable translation mock"},
        ]
