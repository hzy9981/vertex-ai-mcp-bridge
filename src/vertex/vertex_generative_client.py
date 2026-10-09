"""Vertex AI Gemini client using the OpenAI-compatible endpoint."""

import asyncio
import os
from typing import Optional

from openai import OpenAI

from . import auth

SUPPORTED_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]


class VertexGenerativeClient:
    SUPPORTED_MODELS = SUPPORTED_MODELS

    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None):
        project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT is not set")
        self.project_id = project_id
        self.location = location or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
        self.credentials = auth.get_credentials()
        self.base_url = (
            f"https://{self.location}-aiplatform.googleapis.com/v1beta1/"
            f"projects/{self.project_id}/locations/{self.location}/endpoints/openapi"
        )

    def _get_client(self) -> OpenAI:
        # Tokens expire, so build the client with a fresh token per call.
        token = ""
        if self.credentials is not None:
            import google.auth.transport.requests

            self.credentials.refresh(google.auth.transport.requests.Request())
            token = self.credentials.token
        return OpenAI(api_key=token, base_url=self.base_url)

    async def generate_content(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
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

        def _call():
            return self._get_client().chat.completions.create(
                model=f"google/{model}",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

        try:
            response = await asyncio.to_thread(_call)
        except Exception as e:
            raise RuntimeError(f"Error generating content with Vertex AI: {e}") from e
        choice = response.choices[0]
        usage = response.usage
        return {
            "text": choice.message.content,
            "model": model,
            "finish_reason": choice.finish_reason or "stop",
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
