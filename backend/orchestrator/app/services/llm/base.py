"""
File: orchestrator/app/services/llm/base.py
Description: Abstract Base Class, Model Tiers, and Unified Response Schemas
             for the Provider-Agnostic LLM Management Service.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, Type, TypeVar, List
from pydantic import BaseModel, Field


class ModelTier(str, Enum):
    """
    Semantic model tiers for task-based routing.
    Decouples callers from specific vendor model identifiers.
    """
    FAST = "FAST"                # Low latency: typo fixing, coreference rewrite, keyword extraction
    REASONING = "REASONING"      # High capability: 4-Part card decomposition, Socratic hints, math/science
    TRANSLATION = "TRANSLATION"  # Multilingual: Khmer-English pivot translation preserving LaTeX
    DEFAULT = "DEFAULT"          # General fallback tier


class LLMResponse(BaseModel):
    """
    Standardized response container returned across all LLM providers.
    Eliminates vendor-specific response extraction code across the codebase.
    """
    text: str = Field(description="Generated textual content from LLM")
    provider: str = Field(description="Provider name (e.g. gemini, openai, anthropic, ollama, mock)")
    model_name: str = Field(description="Exact model identifier used")
    prompt_tokens: int = Field(default=0, description="Input prompt tokens consumed")
    completion_tokens: int = Field(default=0, description="Output completion tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    latency_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw provider metadata")

    def __str__(self) -> str:
        return self.text


T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """
    Abstract interface that all LLM provider adapters must implement.
    Each provider can maintain its own default temperature configuration.
    """
    def __init__(self, name: str, default_temperature: float = 0.7):
        self.name = name
        self.default_temperature = default_temperature

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        """
        Synchronous text generation.
        If temperature is None, the provider's default configured temperature is used.
        """
        pass

    @abstractmethod
    async def generate_text_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_tier: ModelTier = ModelTier.DEFAULT
    ) -> LLMResponse:
        """
        Asynchronous text generation.
        If temperature is None, the provider's default configured temperature is used.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if provider credentials/client are configured and operational."""
        pass

    def get_active_model(self, tier: ModelTier = ModelTier.DEFAULT) -> str:
        """
        Returns the active model name configured for this provider and tier.
        Defaults to provider name or default_model attribute if present.
        """
        return getattr(self, "default_model", self.name)

    def set_active_model(self, model_name: str, tier: Optional[ModelTier] = None) -> None:
        """
        Dynamically updates the active model name for this provider.
        Subclasses override to support tier-specific model assignment.
        """
        if hasattr(self, "default_model"):
            self.default_model = model_name

    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Returns a catalog or list of available models for this provider.
        """
        return [{"name": self.get_active_model(), "provider": self.name}]

    def get_info(self) -> Dict[str, Any]:
        """
        Returns runtime diagnostic information about this provider adapter.
        """
        return {
            "name": self.name,
            "available": self.is_available(),
            "default_temperature": self.default_temperature,
            "active_model": self.get_active_model(),
        }
