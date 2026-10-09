import asyncio
import threading
from unittest.mock import MagicMock, patch

import pytest

from vertex.deepseek_client import DeepSeekClient
from vertex.vertex_generative_client import VertexGenerativeClient


def run(coro):
    return asyncio.run(coro)


# ---- DeepSeek ----


def test_deepseek_init_with_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = DeepSeekClient(api_key="sk-abc")
    assert client._api_key == "sk-abc"


def test_deepseek_missing_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        client = DeepSeekClient()
        run(client.generate_content("hi"))


def test_deepseek_unsupported_model():
    client = DeepSeekClient(api_key="sk-abc")
    with pytest.raises(ValueError, match="Unsupported model"):
        run(client.generate_content("hi", model="nope"))


def test_deepseek_generate_content_mock(sample_prompt, mock_deepseek_response):
    client = DeepSeekClient(api_key="sk-abc")
    client._client = MagicMock()
    create = client._client.chat.completions.create
    create.return_value = mock_deepseek_response
    result = run(
        client.generate_content(sample_prompt, system_instruction="be brief")
    )
    assert result["text"] == "Hello from DeepSeek"
    assert result["model"] == "deepseek-flash"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 5


def test_deepseek_api_error():
    client = DeepSeekClient(api_key="sk-abc")
    client._client = MagicMock()
    client._client.chat.completions.create.side_effect = Exception("network")
    with pytest.raises(RuntimeError, match="network"):
        run(client.generate_content("hi"))


def test_deepseek_supported_models():
    assert DeepSeekClient.SUPPORTED_MODELS == ("deepseek-flash", "deepseek-v4-pro")


# ---- Vertex ----


@pytest.fixture
def vertex_client(mock_credentials):
    with patch(
        "vertex.vertex_generative_client.auth.get_credentials",
        return_value=mock_credentials,
    ):
        yield VertexGenerativeClient(project_id="proj", location="us-central1")


def test_vertex_init_with_project(vertex_client):
    assert vertex_client.project_id == "proj"
    assert vertex_client.location == "us-central1"
    assert vertex_client._initialized == False


def test_vertex_missing_project(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    client = VertexGenerativeClient()
    assert client.project_id == ""


def test_vertex_unsupported_model(vertex_client):
    with pytest.raises(ValueError, match="Unsupported model"):
        run(vertex_client.generate_content("hi", model="gpt-4"))


def test_vertex_supported_models():
    assert VertexGenerativeClient.SUPPORTED_MODELS == (
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    )


def test_vertex_async_execution(vertex_client, mock_vertex_response):
    """The blocking SDK call must run off the event loop thread."""
    call_threads = []
    mock_obj = MagicMock()

    def fake_generate(prompt, generation_config):
        call_threads.append(threading.get_ident())
        return mock_vertex_response

    async def main():
        loop_thread = threading.get_ident()
        with patch("vertex.vertex_generative_client.GenerativeModel") as mock_gen:
            model_instance = MagicMock()
            model_instance.generate_content.side_effect = fake_generate
            mock_gen.return_value = model_instance
            result = await vertex_client.generate_content("test")
        return loop_thread, result

    loop_thread, result = asyncio.run(main())
    assert result["text"] == "Hello from Vertex"
    assert len(call_threads) > 0
    assert call_threads[0] != loop_thread
