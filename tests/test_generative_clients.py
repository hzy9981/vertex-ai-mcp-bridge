import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vertex import deepseek_client as ds_module
from vertex import vertex_generative_client as vg_module
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
    client = DeepSeekClient()
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        run(client.generate_content("hi"))


def test_deepseek_unsupported_model():
    client = DeepSeekClient(api_key="sk-abc")
    with pytest.raises(ValueError, match="Unsupported model"):
        run(client.generate_content("hi", model="nope"))


def test_deepseek_generate_content_mock(sample_prompt, mock_deepseek_response):
    client = DeepSeekClient(api_key="sk-abc")
    client._client = MagicMock()
    create = AsyncMock(return_value=mock_deepseek_response)
    client._client.chat.completions.create = create
    result = run(
        client.generate_content(sample_prompt, system_instruction="be brief")
    )
    assert result["text"] == "Hello from DeepSeek"
    assert result["model"] == "deepseek-flash"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 5
    kwargs = create.call_args.kwargs
    assert kwargs["messages"][0] == {"role": "system", "content": "be brief"}
    assert kwargs["messages"][1]["content"] == sample_prompt


def test_deepseek_api_error():
    client = DeepSeekClient(api_key="sk-abc")
    client._client = MagicMock()
    client._client.chat.completions.create = AsyncMock(
        side_effect=Exception("network")
    )
    with pytest.raises(RuntimeError, match="network"):
        run(client.generate_content("hi"))


def test_deepseek_supported_models():
    assert ds_module.SUPPORTED_MODELS == ("deepseek-flash", "deepseek-v4-pro")


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
    assert vertex_client._initialized is False


def test_vertex_missing_project(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    client = VertexGenerativeClient()
    assert client.project_id == ""


def test_vertex_unknown_model_warns_and_passes_through(vertex_client, capsys):
    with patch("vertex.vertex_generative_client.GenerativeModel") as mock_gen:
        mock_gen.return_value.generate_content.return_value = _vertex_ok()
        result = run(vertex_client.generate_content("hi", model="gemini-9-future"))
    assert mock_gen.call_args.args[0] == "gemini-9-future"
    assert result["model"] == "gemini-9-future"
    assert "gemini-9-future" in capsys.readouterr().err


def test_vertex_supported_models():
    assert vg_module.SUPPORTED_MODELS == (
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash-lite",
    )


def test_vertex_default_model_is_2_5_flash(vertex_client):
    with patch("vertex.vertex_generative_client.GenerativeModel") as mock_gen:
        mock_gen.return_value.generate_content.return_value = _vertex_ok()
        result = run(vertex_client.generate_content("hi"))
    assert result["model"] == "gemini-2.5-flash"
    assert mock_gen.call_args.args[0] == "gemini-2.5-flash"


def _vertex_ok():
    from types import SimpleNamespace

    return SimpleNamespace(
        candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))],
        text="Hello from Vertex",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12, candidates_token_count=7
        ),
    )


def test_vertex_async_execution(vertex_client):
    """The blocking SDK call must run off the event loop thread."""
    call_threads = []

    def fake_generate(prompt, generation_config):
        call_threads.append(threading.get_ident())
        return _vertex_ok()

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
    assert result["input_tokens"] == 12
    assert result["output_tokens"] == 7
    assert result["finish_reason"] == "STOP"
    assert len(call_threads) == 1
    assert call_threads[0] != loop_thread
