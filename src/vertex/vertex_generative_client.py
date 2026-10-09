"""Vertex AI generative client using the OpenAI-compatible API."""

import sys

import google.auth.transport.requests
from openai import AzureOpenAI

from . import auth

SUPPORTED_MODELS = ("gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash")


class VertexGenerativeClient:
    """Calls Vertex AI Gemini models through the OpenAI SDK."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.endpoint = f"https://{location}-aiplatform.googleapis.com/openai/"
        self._credentials = auth.get_credentials()
        self.client = AzureOpenAI(
            api_version="2024-10-01",
            azure_endpoint=self.endpoint,
            azure_ad_token_provider=self._get_token,
        )

    def _get_token(self) -> str:
        if self._credentials is None:
            raise RuntimeError("No Google Cloud credentials available.")
        if not self._credentials.valid:
            self._credentials.refresh(google.auth.transport.requests.Request())
        return self._credentials.token

    def generate_content(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
        system_instruction: str | None = None,
    ) -> dict:
        """Generate text with a Vertex AI model."""
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
                extra_body={"top_k": top_k},
            )
        except Exception as e:
            msg = f"Error generating content with Vertex AI: {e}"
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
