"""DeepSeek API client using the OpenAI-compatible interface."""

import os
from collections.abc import AsyncIterator

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
AVAILABLE_MODELS = ("deepseek-flash", "deepseek-v4-pro")


def _get_client():
    from openai import AsyncOpenAI

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set.")
    return AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def build_messages(
    prompt: str, system_instruction: str | None = None
) -> list[dict]:
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    return messages


async def chat(
    prompt: str,
    system_instruction: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Non-streaming chat completion; returns the response text."""
    client = _get_client()
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    response = await client.chat.completions.create(
        model=model,
        messages=build_messages(prompt, system_instruction),
        **kwargs,
    )
    return response.choices[0].message.content or ""


async def chat_stream(
    prompt: str,
    system_instruction: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[str]:
    """Streaming chat completion; yields text chunks."""
    client = _get_client()
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    stream = await client.chat.completions.create(
        model=model,
        messages=build_messages(prompt, system_instruction),
        stream=True,
        **kwargs,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
