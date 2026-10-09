"""MCP tools for general-purpose generation via Vertex AI and DeepSeek."""

from typing import Optional

from . import usage_tracker
from .deepseek_client import DeepSeekClient
from .vertex_generative_client import VertexGenerativeClient


async def generate_with_vertex(
    prompt: str,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    top_p: float = 0.95,
    system_instruction: Optional[str] = None,
) -> dict:
    """Generate text with a Gemini model on Vertex AI.

    Args:
        prompt: User prompt.
        model: gemini-2.0-flash, gemini-1.5-pro or gemini-1.5-flash.
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.
        top_p: Top-P sampling.
        system_instruction: Optional system instruction.
    """
    client = VertexGenerativeClient()
    result = await client.generate_content(
        prompt, model, temperature, max_tokens, top_p, system_instruction
    )
    usage_tracker.log_usage(
        "generate_with_vertex", model, prompt, result["text"] or ""
    )
    return result


async def generate_with_deepseek(
    prompt: str,
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    top_p: float = 0.95,
    system_instruction: Optional[str] = None,
) -> dict:
    """Generate text with DeepSeek (OpenAI-compatible API).

    Args:
        prompt: User prompt.
        model: deepseek-chat or deepseek-reasoner.
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.
        top_p: Top-P sampling.
        system_instruction: Optional system instruction.
    """
    client = DeepSeekClient()
    result = await client.generate_content(
        prompt, model, temperature, max_tokens, top_p, system_instruction
    )
    usage_tracker.log_usage(
        "generate_with_deepseek", model, prompt, result["text"] or ""
    )
    return result
