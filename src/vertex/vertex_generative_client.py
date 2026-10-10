"""Generic Vertex AI text generation client (Gemini models)."""

import asyncio
import os
import sys
from typing import Any

import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel

from . import auth

DEFAULT_MODEL = "gemini-2.5-flash"
SUPPORTED_MODELS = ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite")


class VertexGenerativeClient:
    def __init__(self, project_id: str | None = None, location: str | None = None):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
        self.location = location or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return
        try:
            vertexai.init(
                project=self.project_id,
                location=self.location,
                credentials=auth.get_credentials(),
            )
        except Exception as e:
            print(f"Error initializing Vertex AI: {e}", file=sys.stderr)
            raise
        self._initialized = True

    def _generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
        system_instruction: str | None,
    ) -> dict[str, Any]:
        self._init()
        model_obj = GenerativeModel(model, system_instruction=system_instruction)
        config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_tokens,
        )
        response = model_obj.generate_content(prompt, generation_config=config)
        candidates = response.candidates or []
        text = ""
        finish_reason = "UNKNOWN"
        if candidates:
            finish_reason = candidates[0].finish_reason.name
            try:
                text = response.text
            except ValueError:
                text = ""
        usage = response.usage_metadata
        return {
            "text": text,
            "model": model,
            "finish_reason": finish_reason,
            "input_tokens": usage.prompt_token_count if usage else 0,
            "output_tokens": usage.candidates_token_count if usage else 0,
        }

    async def generate_content(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
        system_instruction: str | None = None,
    ) -> dict[str, Any]:
        """Generate text with a Vertex AI Gemini model.

        Unknown model names only log a warning; Vertex validates them.
        """
        if model not in SUPPORTED_MODELS:
            print(
                f"Warning: model '{model}' is not in the known list "
                f"({', '.join(SUPPORTED_MODELS)}); passing it to Vertex AI.",
                file=sys.stderr,
            )
        try:
            return await asyncio.to_thread(
                self._generate,
                prompt, model, temperature, max_tokens, top_p, top_k,
                system_instruction,
            )
        except Exception as e:
            print(f"Vertex generation error: {e}", file=sys.stderr)
            raise RuntimeError(f"Error generating content: {e}") from e
