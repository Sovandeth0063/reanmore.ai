"""
File: backend/testing/unit/gateway/test_llm_runtime_phase0.py
Description: Unit tests for Phase 0 runtime guardrails:
             1. Bounded admission semaphore (LLM_MAX_INFLIGHT = 1).
             2. Single-model retry loop on transient provider failure.
             3. Turn timeout watchdog.
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch

# pyrefly: ignore[missing-import]
from app.services.llm.base import BaseLLMProvider, LLMResponse

# pyrefly: ignore[missing-import]
from app.services.llm.manager import LLMManager


class DummySlowProvider(BaseLLMProvider):
    def __init__(self, delay: float = 0.2):
        super().__init__(name="dummy_slow", default_temperature=0.2)
        self.delay = delay
        self.call_count = 0
        self.max_concurrent_seen = 0
        self._current_inflight = 0

    def is_available(self) -> bool:
        return True

    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        time.sleep(self.delay)
        return LLMResponse(text="response", provider=self.name, model_name="dummy")

    async def generate_text_async(self, prompt: str, **kwargs) -> LLMResponse:
        self._current_inflight += 1
        if self._current_inflight > self.max_concurrent_seen:
            self.max_concurrent_seen = self._current_inflight
        self.call_count += 1
        await asyncio.sleep(self.delay)
        self._current_inflight -= 1
        return LLMResponse(text=f"response to: {prompt}", provider=self.name, model_name="dummy")


class FlakyProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(name="flaky", default_temperature=0.2)
        self.attempts = 0

    def is_available(self) -> bool:
        return True

    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(text="ok", provider=self.name, model_name="flaky")

    async def generate_text_async(self, prompt: str, **kwargs) -> LLMResponse:
        self.attempts += 1
        if self.attempts == 1:
            raise RuntimeError("Transient connection reset")
        return LLMResponse(text="recovered on retry", provider=self.name, model_name="flaky")


@pytest.mark.asyncio
async def test_semaphore_bounds_concurrent_requests():
    """Verify that multiple concurrent async requests are bounded by LLM_MAX_INFLIGHT=1."""
    manager = LLMManager()
    dummy = DummySlowProvider(delay=0.1)
    manager._providers = {"dummy": dummy}
    manager.primary_provider_name = "dummy"
    manager.fallback_provider_name = None
    manager._semaphore = asyncio.Semaphore(1)

    # Launch 3 concurrent requests
    t1 = time.time()
    results = await asyncio.gather(
        manager.generate_text_async("task 1"),
        manager.generate_text_async("task 2"),
        manager.generate_text_async("task 3"),
    )
    total_elapsed = time.time() - t1

    assert len(results) == 3
    assert all("response to:" in r.text for r in results)
    # Since semaphore is 1, max concurrent executions inside provider must strictly be 1
    assert dummy.max_concurrent_seen == 1
    assert dummy.call_count == 3
    # Total elapsed time must be at least 3 * 0.1s = 0.3s
    assert total_elapsed >= 0.28


@pytest.mark.asyncio
async def test_single_model_retry_loop_recovers():
    """Verify that a transient error triggers a single retry and succeeds on attempt 2."""
    manager = LLMManager()
    flaky = FlakyProvider()
    manager._providers = {"flaky": flaky}
    manager.primary_provider_name = "flaky"
    manager.fallback_provider_name = None

    resp = await manager.generate_text_async("hello")
    assert resp.text == "recovered on retry"
    assert flaky.attempts == 2


@pytest.mark.asyncio
async def test_turn_timeout_triggers_exception():
    """Verify that a slow request exceeding total turn timeout raises an error."""
    manager = LLMManager()
    dummy_super_slow = DummySlowProvider(delay=1.0)
    manager._providers = {"slow": dummy_super_slow}
    manager.primary_provider_name = "slow"
    manager.fallback_provider_name = None
    manager._total_turn_timeout = 0.1  # Very short timeout

    with pytest.raises(Exception):
        await manager.generate_text_async("will time out")
