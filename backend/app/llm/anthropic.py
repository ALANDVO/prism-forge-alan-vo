"""
Anthropic Messages API Adapter

Supports Anthropic's Claude models via the Messages API.
"""
from typing import Optional

import httpx

from .base import LLMAdapter, LLMMessage, LLMResponse, LLMProviderError


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic Messages API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        super().__init__(api_key, model, base_url, timeout)
        self.base_url = base_url or "https://api.anthropic.com/v1"

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        url = f"{self.base_url}/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # Separate system message from conversation
        system_messages = [m.content for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in conversation],
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }

        if system_messages:
            payload["system"] = "\n\n".join(system_messages)

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["content"][0]["text"],
                model=data.get("model", self.model),
                usage=data.get("usage"),
                finish_reason=data.get("stop_reason"),
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                self._redact_error(f"HTTP {e.response.status_code}: {e.response.text}"),
                "anthropic",
                e.response.status_code,
            )
        except httpx.RequestError as e:
            raise LLMProviderError(
                self._redact_error(f"Request failed: {e}"),
                "anthropic",
            )
        except (KeyError, IndexError) as e:
            raise LLMProviderError(
                f"Invalid response format: {e}",
                "anthropic",
            )