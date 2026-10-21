"""
Google Gemini generateContent API Adapter

Supports Google's Gemini models via the generateContent API.
"""
from typing import Optional

import httpx

from .base import LLMAdapter, LLMMessage, LLMResponse, LLMProviderError


class GeminiAdapter(LLMAdapter):
    """Adapter for Google Gemini generateContent API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        super().__init__(api_key, model, base_url, timeout)
        self.base_url = base_url or "https://generativelanguage.googleapis.com/v1beta"

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        headers = {
            "Content-Type": "application/json",
        }

        # Convert messages to Gemini format
        contents = []
        for m in messages:
            role = "user" if m.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.content}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens"),
            }
        }

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            candidate = data["candidates"][0]
            return LLMResponse(
                content=candidate["content"]["parts"][0]["text"],
                model=self.model,
                usage=data.get("usageMetadata"),
                finish_reason=candidate.get("finishReason"),
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                self._redact_error(f"HTTP {e.response.status_code}: {e.response.text}"),
                "gemini",
                e.response.status_code,
            )
        except httpx.RequestError as e:
            raise LLMProviderError(
                self._redact_error(f"Request failed: {e}"),
                "gemini",
            )
        except (KeyError, IndexError) as e:
            raise LLMProviderError(
                f"Invalid response format: {e}",
                "gemini",
            )