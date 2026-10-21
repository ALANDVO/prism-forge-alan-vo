"""
LLM Adapter Factory

Creates provider-specific adapters based on configuration.
"""
from typing import Optional

from app.core.config import get_settings

from .base import LLMAdapter
from .openai_compatible import OpenAICompatibleAdapter
from .anthropic import AnthropicAdapter
from .gemini import GeminiAdapter


def create_llm_adapter(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMAdapter:
    """
    Create an LLM adapter based on provider configuration.

    Args:
        provider: LLM provider name (openai-compatible, anthropic, gemini, ollama)
        model: Model name
        api_key: API key
        base_url: Base URL for the provider API

    Returns:
        Configured LLMAdapter instance

    Raises:
        ValueError: If provider is unknown or required config missing
    """
    settings = get_settings()

    provider = provider or settings.llm_provider
    model = model or settings.llm_model
    api_key = api_key or settings.llm_api_key
    base_url = base_url or settings.llm_base_url

    if not api_key:
        raise ValueError("LLM API key not configured")

    if not model:
        raise ValueError("LLM model not configured")

    provider = provider.lower()

    if provider in ("openai", "openai-compatible", "litellm", "openrouter", "ollama"):
        return OpenAICompatibleAdapter(
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
    elif provider in ("anthropic", "claude"):
        return AnthropicAdapter(
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
    elif provider in ("gemini", "google"):
        return GeminiAdapter(
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")