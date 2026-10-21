# LLM Adapters Package
"""
Pluggable LLM provider adapters for Prism Forge.

Supports:
- OpenAI-compatible (including LiteLLM, OpenRouter, Ollama)
- Anthropic Messages API
- Google Gemini generateContent API

__all__ = [
    "LLMAdapter",
    "LLMMessage",
    "LLMResponse",
    "OpenAICompatibleAdapter",
    "AnthropicAdapter",
    "GeminiAdapter",
    "create_llm_adapter",
]
"""
from .base import LLMAdapter, LLMMessage, LLMResponse
from .openai_compatible import OpenAICompatibleAdapter
from .anthropic import AnthropicAdapter
from .gemini import GeminiAdapter

__all__ = [
    "LLMAdapter",
    "LLMMessage",
    "LLMResponse",
    "OpenAICompatibleAdapter",
    "AnthropicAdapter",
    "GeminiAdapter",
]