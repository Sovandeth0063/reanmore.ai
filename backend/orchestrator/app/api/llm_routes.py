"""
File: orchestrator/app/api/llm_routes.py
Description: REST API Endpoints for the Dynamic LLM Controller.
             Enables runtime provider/model switching, auto-discovery of local/remote models,
             connectivity tests, and full observability without restarting services.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.llm import llm_service, ModelTier
from app.core.logging import logger

llm_router = APIRouter(prefix="/llm", tags=["LLM Controller"])


class SwitchProviderRequest(BaseModel):
    provider: str = Field(description="Target primary LLM provider (e.g. 'gemini', 'ollama', 'openai', 'mock')")
    fallback: Optional[str] = Field(default=None, description="Optional fallback provider (e.g. 'ollama', 'gemini', 'mock')")
    model: Optional[str] = Field(default=None, description="Optional model to activate for the provider (e.g. 'qwen3.5:4b', 'gemma4:e4b')")
    tier: Optional[str] = Field(default=None, description="Optional tier to assign model to ('FAST', 'REASONING', 'TRANSLATION', 'DEFAULT')")


class SwitchModelRequest(BaseModel):
    provider: str = Field(description="Target provider name")
    model: str = Field(description="Target model name")
    tier: Optional[str] = Field(default=None, description="Optional tier ('FAST', 'REASONING', 'TRANSLATION', 'DEFAULT')")


class SetEndpointRequest(BaseModel):
    provider: str = Field(description="Target provider name (e.g. 'ollama')")
    base_url: str = Field(description="Target endpoint URL (e.g. 'http://localhost:11434' or 'https://ollama.com')")
    api_key: Optional[str] = Field(default=None, description="Optional API key or bearer token")


class TestGenerationRequest(BaseModel):
    prompt: str = Field(default="Hello! Please confirm you are online.", description="Test prompt to run")
    provider: Optional[str] = Field(default=None, description="Specific provider to test (defaults to primary)")
    model: Optional[str] = Field(default=None, description="Specific model to test")
    tier: str = Field(default="DEFAULT", description="Tier to run under ('FAST', 'REASONING', 'TRANSLATION', 'DEFAULT')")


@llm_router.get("/status")
def get_llm_status():
    """
    Returns the real-time status of all registered LLM providers,
    active primary and fallback selections, and current model bindings.
    """
    try:
        return llm_service.get_status()
    except Exception as e:
        logger.error(f"Error fetching LLM status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@llm_router.get("/models")
def get_available_models():
    """
    Returns discovered models across all providers,
    including live querying of local Ollama /api/tags and cloud catalogs.
    """
    try:
        catalog = llm_service.list_all_models()
        return {
            "status": "success",
            "models": catalog
        }
    except Exception as e:
        logger.error(f"Error fetching LLM models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@llm_router.post("/switch")
def switch_llm_configuration(req: SwitchProviderRequest):
    """
    Switches active primary provider, optional fallback provider,
    and optional active model in real-time with zero service downtime.
    """
    try:
        # 1. Switch model if specified
        if req.model:
            tier_enum = None
            if req.tier:
                try:
                    tier_enum = ModelTier[req.tier.upper()]
                except KeyError:
                    pass
            llm_service.switch_model(req.provider, req.model, tier=tier_enum)

        # 2. Switch provider
        result = llm_service.switch_provider(req.provider, fallback_provider=req.fallback)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error switching LLM configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@llm_router.post("/model")
def switch_provider_model(req: SwitchModelRequest):
    """
    Updates the active model for a specific provider and tier.
    """
    try:
        tier_enum = None
        if req.tier:
            try:
                tier_enum = ModelTier[req.tier.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid tier '{req.tier}'. Valid: {[t.value for t in ModelTier]}")
        
        result = llm_service.switch_model(req.provider, req.model, tier=tier_enum)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@llm_router.post("/endpoint")
def set_provider_endpoint_route(req: SetEndpointRequest):
    """
    Updates the base URL and API key for a provider (e.g. Ollama Local vs Cloud).
    """
    try:
        result = llm_service.set_provider_endpoint(req.provider, req.base_url, api_key=req.api_key)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except NotImplementedError as nie:
        raise HTTPException(status_code=405, detail=str(nie))
    except Exception as e:
        logger.error(f"Error setting provider endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@llm_router.post("/test")
def test_generation_route(req: TestGenerationRequest):
    """
    Dry-runs a test generation against a specified or active LLM provider and model.
    Measures latency, token usage, and reports errors without altering production traffic.
    """
    tier_enum = ModelTier.DEFAULT
    try:
        tier_enum = ModelTier[req.tier.upper()]
    except KeyError:
        pass

    result = llm_service.test_generation(
        prompt=req.prompt,
        provider_name=req.provider,
        model_name=req.model,
        model_tier=tier_enum
    )
    return result
