"""DeepSeek client using the OpenAI-compatible API."""

import logging
import os
import sys

from openai import OpenAI

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
SUPPORTED_MODELS = ("deepseek-flash", "deepseek-v4-pro")


class DeepSeekClient:
    """Calls DeepSeek models through the OpenAI SDK."""

    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    def generate_content(
        self,
        prompt: str,
        model: str = "deepseek-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        system_instruction: str | None = None,
    ) -> dict:
        """Generate text with a DeepSeek model."""
        if model not in SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model '{model}'. "
                f"Supported: {', '.join(SUPPORTED_MODELS)}"
            )
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
        except Exception as e:
            msg = f"Error generating content with DeepSeek: {e}"
            logger.error(msg)
            print(msg, file=sys.stderr)
            raise RuntimeError(msg) from e
        choice = response.choices[0]
        usage = response.usage
        return {
            "text": choice.message.content or "",
            "model": model,
            "finish_reason": choice.finish_reason or "stop",
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
