"""
Base LLM Adapter Interface

All provider adapters must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import httpx


@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None


class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """
        Send a chat completion request.

        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific options (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with the assistant's reply

        Raises:
            LLMProviderError: On provider errors
        """
        pass

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _redact_error(self, error: Exception) -> str:
        """Redact sensitive info from error messages."""
        error_str = str(error)
        # Redact API key if present
        if self.api_key and self.api_key in error_str:
            error_str = error_str.replace(self.api_key, "***REDACTED***")
        return error_str


class LLMProviderError(Exception):
    """Raised when LLM provider returns an error."""

    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code