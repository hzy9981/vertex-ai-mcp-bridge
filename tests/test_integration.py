import asyncio
from unittest.mock import MagicMock, patch

import pytest

from vertex import generative_tools, usage_tracker
from vertex.deepseek_client import DeepSeekClient
from vertex.vertex_generative_client import VertexGenerativeClient


@pytest.fixture
def tmp_usage_db(tmp_path, monkeypatch):
    monkeypatch.setattr(usage_tracker, "DB_PATH", str(tmp_path / "usage.db"))
    usage_tracker.init_db()
    # Avoid downloading tiktoken encodings (offline-safe)
    monkeypatch.setattr(
        usage_tracker, "count_tokens", lambda text, model="": len(text.split())
    )


def test_deepseek_api_key_from_env(env_with_keys):
    client = DeepSeekClient()
    assert client.client.api_key == env_with_keys["DEEPSEEK_API_KEY"]


def test_vertex_project_from_env(env_with_keys, mock_credentials):
    with patch(
        "vertex.vertex_generative_client.auth.get_credentials",
        return_value=mock_credentials,
    ):
        client = VertexGenerativeClient()
    assert client.project_id == "test-project"
    assert client.location == "us-central1"


def test_generate_with_vertex_tool(
    env_with_keys, mock_vertex_response, tmp_usage_db
):
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = mock_vertex_response
    with patch(
        "vertex.vertex_generative_client.auth.get_credentials",
        return_value=None,
    ), patch.object(
        VertexGenerativeClient, "_get_client", return_value=mock_openai
    ):
        result = asyncio.run(generative_tools.generate_with_vertex("hello"))
    assert result["text"] == "Hello from Vertex"
    assert result["input_tokens"] == 12


def test_generate_with_deepseek_tool(
    env_with_keys, mock_deepseek_response, tmp_usage_db
):
    with patch("vertex.deepseek_client.OpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create.return_value = (
            mock_deepseek_response
        )
        result = asyncio.run(generative_tools.generate_with_deepseek("hello"))
    assert result["text"] == "Hello from DeepSeek"
    assert result["output_tokens"] == 5


def test_generate_tool_missing_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError):
        asyncio.run(generative_tools.generate_with_deepseek("hello"))


def test_tools_registered_with_mcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        pytest.skip("FastMCP (mcp 1.x) not available")

    mcp = FastMCP("t")
    mcp.add_tool(generative_tools.generate_with_vertex)
    mcp.add_tool(generative_tools.generate_with_deepseek)
    names = {t.name for t in mcp._tool_manager.list_tools()}
    assert {"generate_with_vertex", "generate_with_deepseek"} <= names


def test_usage_tracking_integration(
    env_with_keys, mock_deepseek_response, tmp_usage_db
):
    before = usage_tracker.get_stats()
    with patch("vertex.deepseek_client.OpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create.return_value = (
            mock_deepseek_response
        )
        asyncio.run(generative_tools.generate_with_deepseek("hello world"))
    after = usage_tracker.get_stats()
    assert after["request_count"] == before["request_count"] + 1
    assert after["total_tokens"] > before["total_tokens"]
    assert after["input_tokens"] > 0 and after["output_tokens"] > 0
