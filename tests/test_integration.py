import asyncio
from unittest.mock import MagicMock, patch

import pytest

from vertex.deepseek_client import DeepSeekClient
from vertex.vertex_generative_client import VertexGenerativeClient


def test_deepseek_api_key_from_env(env_with_keys):
    client = DeepSeekClient()
    assert client._api_key is None
    # Key is read on first call
    assert env_with_keys["DEEPSEEK_API_KEY"] == "sk-test-key"


def test_vertex_project_from_env(env_with_keys, mock_credentials):
    with patch(
        "vertex.vertex_generative_client.auth.get_credentials",
        return_value=mock_credentials,
    ):
        client = VertexGenerativeClient()
    assert client.project_id == "test-project"
    assert client.location == "us-central1"


def test_deepseek_models_available():
    """Verify DeepSeek has required models."""
    assert "deepseek-flash" in DeepSeekClient.SUPPORTED_MODELS
    assert "deepseek-v4-pro" in DeepSeekClient.SUPPORTED_MODELS


def test_vertex_models_available():
    """Verify Vertex has required models."""
    assert "gemini-2.0-flash" in VertexGenerativeClient.SUPPORTED_MODELS
    assert "gemini-1.5-pro" in VertexGenerativeClient.SUPPORTED_MODELS
    assert "gemini-1.5-flash" in VertexGenerativeClient.SUPPORTED_MODELS


def test_openai_sdk_installed():
    """Verify openai SDK is available."""
    try:
        from openai import AsyncOpenAI
        assert AsyncOpenAI is not None
    except ImportError:
        pytest.skip("openai SDK not installed")
