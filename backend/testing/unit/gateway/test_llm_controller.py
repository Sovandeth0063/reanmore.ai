"""
File: testing/unit/gateway/test_llm_controller.py
Description: Comprehensive Unit Test Suite for the Dynamic LLM Controller.
             Verifies:
             1. Controller singleton initialization and inheritance from LLMManager.
             2. Zero-downtime runtime provider switching (Gemini, Ollama, Mock, OpenAI).
             3. Dynamic model switching per tier and globally (e.g. qwen3.5:4b, gemma4:e4b).
             4. Catalog discovery across providers.
             5. Status inspection and listener notifications.
             6. Isolated test generation dry-runs.
             7. FastAPI REST API endpoints (/api/llm/status, /api/llm/switch, /api/llm/models, /api/llm/test).
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "orchestrator")))

# pyrefly: ignore [missing-import]
from app.services.llm import (
    llm_service,
    llm_controller,
    LLMController,
    LLMManager,
    ModelTier,
    LLMResponse,
)
# pyrefly: ignore [missing-import]
from app.services.llm.providers.mock_provider import MockLLMProvider
# pyrefly: ignore [missing-import]
from app.services.llm.providers.ollama_provider import OllamaProvider
# pyrefly: ignore [missing-import]
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_controller_singleton_and_inheritance():
    """Verifies llm_controller and llm_service are identical LLMController instances."""
    assert isinstance(llm_controller, LLMController)
    assert isinstance(llm_controller, LLMManager)
    assert llm_service is llm_controller
    assert "mock" in llm_controller.get_registered_providers()
    assert "ollama" in llm_controller.get_registered_providers()
    assert "gemini" in llm_controller.get_registered_providers()


def test_runtime_provider_switching():
    """Verifies instantaneous provider swapping with zero code change in callers."""
    original_primary = llm_controller.primary_provider_name
    original_fallback = llm_controller.fallback_provider_name

    try:
        # Register a distinguishable mock
        test_provider = MockLLMProvider(default_response="Response from TestMockProvider")
        llm_controller.register_provider("test_mock", test_provider)

        # Switch primary to test_mock
        res = llm_controller.switch_provider("test_mock", fallback_provider="mock")
        assert res["status"] == "success"
        assert llm_controller.primary_provider_name == "test_mock"
        assert llm_controller.fallback_provider_name == "mock"

        # Standard caller invokes llm_service without knowing underlying provider
        resp = llm_service.generate_text("Explain photosynthesis")
        assert isinstance(resp, LLMResponse)
        assert resp.text == "Response from TestMockProvider"
        assert resp.provider == "mock"
    finally:
        llm_controller.primary_provider_name = original_primary
        llm_controller.fallback_provider_name = original_fallback


def test_switch_provider_invalid():
    """Attempting to switch to an unknown provider raises a descriptive ValueError."""
    with pytest.raises(ValueError, match="Unknown LLM provider 'non_existent_provider'"):
        llm_controller.switch_provider("non_existent_provider")


def test_dynamic_model_switching_per_tier():
    """Tests switching models for a provider globally and per ModelTier."""
    ollama_p = llm_controller.get_provider("ollama")
    assert ollama_p is not None

    original_default = ollama_p.default_model
    original_reasoning = getattr(ollama_p, "reasoning_model_name", original_default)

    try:
        # 1. Switch global default model
        res = llm_controller.switch_model("ollama", "qwen3.5:4b")
        assert res["status"] == "success"
        assert ollama_p.get_active_model(ModelTier.DEFAULT) == "qwen3.5:4b"

        # 2. Switch tier-specific model for REASONING
        res_tier = llm_controller.switch_model("ollama", "gemma4:e4b", tier=ModelTier.REASONING)
        assert res_tier["status"] == "success"
        assert ollama_p.get_active_model(ModelTier.REASONING) == "gemma4:e4b"
        assert ollama_p.get_active_model(ModelTier.FAST) == "qwen3.5:4b"
    finally:
        ollama_p.default_model = original_default
        ollama_p.fast_model_name = original_default
        ollama_p.reasoning_model_name = original_reasoning
        ollama_p.translation_model_name = original_default


def test_controller_status_diagnostic():
    """Verifies get_status returns complete provider metadata and configuration."""
    status = llm_controller.get_status()
    assert "primary_provider" in status
    assert "fallback_provider" in status
    assert "active_model" in status
    assert "providers" in status
    assert "registered_providers" in status

    # Verify Ollama status structure
    if "ollama" in status["providers"]:
        ollama_info = status["providers"]["ollama"]
        assert "available" in ollama_info
        assert "models_by_tier" in ollama_info
        assert "FAST" in ollama_info["models_by_tier"]
        assert "REASONING" in ollama_info["models_by_tier"]


def test_list_all_models_discovery():
    """Verifies model catalog aggregation across registered providers."""
    catalog = llm_controller.list_all_models()
    assert isinstance(catalog, dict)
    assert "mock" in catalog
    assert len(catalog["mock"]) >= 1
    assert any(m["name"] == "mock-fast" for m in catalog["mock"])


def test_listener_event_notification():
    """Verifies subscribers receive events on configuration changes."""
    events = []

    def on_llm_change(event_type: str, data: dict):
        events.append((event_type, data))

    llm_controller.add_listener(on_llm_change)

    original_primary = llm_controller.primary_provider_name
    try:
        llm_controller.switch_provider("mock")
        llm_controller.switch_model("mock", "custom-mock-model")

        assert len(events) >= 2
        assert events[0][0] == "provider_switched"
        assert events[0][1]["new_primary"] == "mock"
        assert events[1][0] == "model_switched"
        assert events[1][1]["new_model"] == "custom-mock-model"
    finally:
        llm_controller.primary_provider_name = original_primary


def test_test_generation_isolated():
    """Verifies dry-run test generation with mock provider."""
    res = llm_controller.test_generation(
        prompt="Ping",
        provider_name="mock"
    )
    assert res["success"] is True
    assert res["provider"] == "mock"
    assert "response_text" in res
    assert res["latency_ms"] >= 0.0


def test_set_provider_endpoint():
    """Verifies updating base URL on Ollama provider."""
    ollama_p = llm_controller.get_provider("ollama")
    if ollama_p:
        orig_url = ollama_p.base_url
        try:
            res = llm_controller.set_provider_endpoint("ollama", "http://localhost:11434")
            assert res["status"] == "success"
            assert ollama_p.base_url == "http://localhost:11434"
        finally:
            ollama_p.base_url = orig_url


# -------------------------------------------------------------------------
# REST API Endpoint Tests
# -------------------------------------------------------------------------

def test_api_llm_status_endpoint(client):
    resp = client.get("/api/llm/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "primary_provider" in data
    assert "fallback_provider" in data
    assert "providers" in data


def test_api_llm_models_endpoint(client):
    resp = client.get("/api/llm/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "mock" in data["models"]


def test_api_llm_switch_endpoint(client):
    original_primary = llm_controller.primary_provider_name
    try:
        resp = client.post("/api/llm/switch", json={
            "provider": "mock",
            "fallback": "mock"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert llm_controller.primary_provider_name == "mock"
    finally:
        llm_controller.primary_provider_name = original_primary


def test_api_llm_model_endpoint(client):
    resp = client.post("/api/llm/model", json={
        "provider": "mock",
        "model": "mock-test-model",
        "tier": "FAST"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"


def test_api_llm_test_endpoint(client):
    resp = client.post("/api/llm/test", json={
        "prompt": "Hello mock",
        "provider": "mock",
        "tier": "DEFAULT"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["provider"] == "mock"
