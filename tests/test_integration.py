from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import pytest

from vertex import deepseek_client as ds_module
from vertex import vertex_generative_client as vg_module
from vertex.deepseek_client import DeepSeekClient
from vertex.vertex_generative_client import VertexGenerativeClient


def test_deepseek_api_key_from_env(env_with_keys, mock_deepseek_response):
    client = DeepSeekClient()
    assert client._api_key is None
    with patch("vertex.deepseek_client.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create = AsyncMock(
            return_value=mock_deepseek_response
        )
        result = asyncio.run(client.generate_content("hi"))
    assert mock_openai.call_args.kwargs["api_key"] == "sk-test-key"
    assert mock_openai.call_args.kwargs["base_url"] == ds_module.DEEPSEEK_BASE_URL
    assert result["text"] == "Hello from DeepSeek"


def test_vertex_project_from_env(env_with_keys):
    client = VertexGenerativeClient()
    assert client.project_id == "test-project"
    assert client.location == "us-central1"


def test_vertex_init_uses_credentials(env_with_keys, mock_credentials):
    client = VertexGenerativeClient()
    with patch(
        "vertex.vertex_generative_client.auth.get_credentials",
        return_value=mock_credentials,
    ), patch("vertex.vertex_generative_client.vertexai.init") as mock_init:
        client._init()
        client._init()
    mock_init.assert_called_once_with(
        project="test-project",
        location="us-central1",
        credentials=mock_credentials,
    )


def test_deepseek_models_available():
    assert ds_module.SUPPORTED_MODELS == ("deepseek-flash", "deepseek-v4-pro")


def test_vertex_models_available():
    assert vg_module.DEFAULT_MODEL == "gemini-2.5-flash"
    for name in ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"):
        assert name in vg_module.SUPPORTED_MODELS
    assert not any(m.startswith(("gemini-1.5", "gemini-2.0")) for m in vg_module.SUPPORTED_MODELS)


def test_openai_sdk_installed():
    pytest.importorskip("openai")
