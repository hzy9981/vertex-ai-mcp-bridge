import asyncio
import threading
from unittest.mock import MagicMock, patch

import pytest

from vertex.deepseek_client import DeepSeekClient
from vertex.vertex_generative_client import VertexGenerativeClient


def run(coro):
    return asyncio.run(coro)


# ---------------- DeepSeek ----------------


def test_deepseek_init_with_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = DeepSeekClient(api_key="sk-abc")
    assert client.client.api_key == "sk-abc"


def test_deepseek_missing_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient()


def test_deepseek_unsupported_model():
    client = DeepSeekClient(api_key="sk-abc")
    with pytest.raises(ValueError, match="Unsupported model"):
        run(client.generate_content("hi", model="nope"))


def test_deepseek_generate_content_mock(
    sample_prompt, mock_deepseek_response
):
    client = DeepSeekClient(api_key="sk-abc")
    client.client = MagicMock()
    create = client.client.chat.completions.create
    create.return_value = mock_deepseek_response
    result = run(
        client.generate_content(sample_prompt, system_instruction="be brief")
    )
    assert result == {
        "text": "Hello from DeepSeek",
        "model": "deepseek-chat",
        "finish_reason": "stop",
        "input_tokens": 10,
        "output_tokens": 5,
    }
    kwargs = create.call_args.kwargs
    assert kwargs["messages"] == [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": sample_prompt},
    ]
    assert kwargs["temperature"] == 0.7
    assert kwargs["max_tokens"] == 1024


def test_deepseek_api_error():
    client = DeepSeekClient(api_key="sk-abc")
    client.client = MagicMock()
    client.client.chat.completions.create.side_effect = Exception("network")
    with pytest.raises(RuntimeError, match="network"):
        run(client.generate_content("hi"))


def test_deepseek_supported_models():
    assert DeepSeekClient.SUPPORTED_MODELS == [
        "deepseek-chat",
        "deepseek-reasoner",
    ]


# ---------------- Vertex ----------------


@pytest.fixture
def vertex_client(mock_credentials):
    with patch(
        "vertex.vertex_generative_client.auth.get_credentials",
        return_value=mock_credentials,
    ):
        yield VertexGenerativeClient(project_id="proj", location="europe-west1")


def test_vertex_init_with_project(vertex_client):
    assert vertex_client.project_id == "proj"
    assert vertex_client.location == "europe-west1"
    assert "europe-west1-aiplatform.googleapis.com" in vertex_client.base_url
    assert "projects/proj" in vertex_client.base_url


def test_vertex_missing_project(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT"):
        VertexGenerativeClient()


def test_vertex_unsupported_model(vertex_client):
    with pytest.raises(ValueError, match="Unsupported model"):
        run(vertex_client.generate_content("hi", model="gpt-4"))


def test_vertex_generate_content_mock(
    vertex_client, sample_prompt, mock_vertex_response
):
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = mock_vertex_response
    with patch.object(vertex_client, "_get_client", return_value=mock_openai):
        result = run(
            vertex_client.generate_content(
                sample_prompt, model="gemini-1.5-pro", system_instruction="s"
            )
        )
    assert result["text"] == "Hello from Vertex"
    assert result["model"] == "gemini-1.5-pro"
    assert result["input_tokens"] == 12
    assert result["output_tokens"] == 7
    kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "google/gemini-1.5-pro"
    assert kwargs["messages"][0] == {"role": "system", "content": "s"}


def test_vertex_supported_models():
    assert VertexGenerativeClient.SUPPORTED_MODELS == [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]


def test_vertex_async_execution(vertex_client, mock_vertex_response):
    """The blocking SDK call must run off the event loop thread."""
    call_threads = []
    mock_openai = MagicMock()

    def fake_create(**kwargs):
        call_threads.append(threading.get_ident())
        return mock_vertex_response

    mock_openai.chat.completions.create.side_effect = fake_create

    async def main():
        loop_thread = threading.get_ident()
        with patch.object(
            vertex_client, "_get_client", return_value=mock_openai
        ):
            results = await asyncio.gather(
                vertex_client.generate_content("a"),
                vertex_client.generate_content("b"),
            )
        return loop_thread, results

    loop_thread, results = asyncio.run(main())
    assert len(results) == 2
    assert all(t != loop_thread for t in call_threads)
