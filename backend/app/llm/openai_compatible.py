"""
OpenAI-compatible LLM Adapter

Supports OpenAI API, LiteLLM, OpenRouter, Ollama, and other compatible endpoints.
"""
import json
from typing import Optional

import httpx

from .base import LLMAdapter, LLMMessage, LLMResponse, LLMProviderError


class OpenAICompatibleAdapter(LLMAdapter):
    """Adapter for OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        super().__init__(api_key, model, base_url, timeout)
        self.base_url = base_url or "https://api.openai.com/v1"

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens"),
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.model),
                usage=data.get("usage"),
                finish_reason=choice.get("finish_reason"),
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                self._redact_error(f"HTTP {e.response.status_code}: {e.response.text}"),
                "openai-compatible",
                e.response.status_code,
            )
        except httpx.RequestError as e:
            raise LLMProviderError(
                self._redact_error(f"Request failed: {e}"),
                "openai-compatible",
            )
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMProviderError(
                f"Invalid response format: {e}",
                "openai-compatible",
            )