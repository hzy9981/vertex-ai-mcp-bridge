from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _make_response(text, prompt_tokens, completion_tokens, finish="stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=text), finish_reason=finish
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    )


@pytest.fixture
def mock_deepseek_response():
    return _make_response("Hello from DeepSeek", 10, 5)


@pytest.fixture
def mock_vertex_response():
    return _make_response("Hello from Vertex", 12, 7)


@pytest.fixture
def sample_prompt():
    return "What is the capital of France?"


@pytest.fixture
def env_with_keys(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    return {
        "DEEPSEEK_API_KEY": "sk-test-key",
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "GOOGLE_CLOUD_LOCATION": "us-central1",
    }


@pytest.fixture
def mock_credentials():
    creds = MagicMock()
    creds.token = "fake-token"
    return creds

collect_ignore = ["manual_test.py"]
