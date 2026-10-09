"""DeepSeek API client using the OpenAI-compatible interface."""

import os
import sys
from typing import Any

from openai import AsyncOpenAI

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
SUPPORTED_MODELS = ("deepseek-flash", "deepseek-v4-pro")


class DeepSeekClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            api_key = self._api_key or os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set.")
            self._client = AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        return self._client

    async def generate_content(
        self,
        prompt: str,
        model: str = "deepseek-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        system_instruction: str | None = None,
    ) -> dict[str, Any]:
        """Generate text with a DeepSeek model."""
        if model not in SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model '{model}'. Supported: {', '.join(SUPPORTED_MODELS)}"
            )
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        try:
            response = await self._get_client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
        except Exception as e:
            print(f"DeepSeek API error: {e}", file=sys.stderr)
            raise RuntimeError(f"Error calling DeepSeek API: {e}") from e
        choice = response.choices[0]
        usage = response.usage
        return {
            "text": choice.message.content or "",
            "model": model,
            "finish_reason": choice.finish_reason or "UNKNOWN",
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
