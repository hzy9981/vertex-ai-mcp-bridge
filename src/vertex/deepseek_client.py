"""DeepSeek client using the OpenAI-compatible API."""

import asyncio
import os
from typing import Optional

from openai import OpenAI

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
SUPPORTED_MODELS = ["deepseek-chat", "deepseek-reasoner"]


class DeepSeekClient:
    SUPPORTED_MODELS = SUPPORTED_MODELS

    def __init__(self, api_key: Optional[str] = None, base_url: str = DEEPSEEK_BASE_URL):
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    async def generate_content(
        self,
        prompt: str,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        system_instruction: Optional[str] = None,
    ) -> dict:
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model '{model}'. Supported: {self.SUPPORTED_MODELS}"
            )
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
        except Exception as e:
            raise RuntimeError(f"Error generating content with DeepSeek: {e}") from e
        choice = response.choices[0]
        usage = response.usage
        return {
            "text": choice.message.content,
            "model": model,
            "finish_reason": choice.finish_reason or "stop",
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
