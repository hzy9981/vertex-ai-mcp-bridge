import json

import pytest
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from vertex.openai_compat import handle_chat_completions

HEADERS = {"Authorization": "Bearer key-1"}


def _client(calls, result=None, fail=False):
    async def call_tool(name, args):
        calls.append((name, args))
        if fail:
            raise RuntimeError("boom")
        return result or {"text": "Hello world, this is a long reply!", "finish_reason": "stop",
                          "input_tokens": 3, "output_tokens": 4}

    async def endpoint(request):
        return await handle_chat_completions(request, call_tool)

    return TestClient(Starlette(routes=[Route("/v1/chat/completions", endpoint, methods=["POST"])]))


BODY = {"model": "gemini-2.5-flash", "messages": [{"role": "user", "content": "Hi"}]}


def test_disabled_returns_501(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    assert _client([]).post("/v1/chat/completions", json=BODY, headers=HEADERS).status_code == 501


def test_auth(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "key-0, key-1")
    c = _client([])
    assert c.post("/v1/chat/completions", json=BODY).status_code == 401
    assert c.post("/v1/chat/completions", json=BODY, headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert c.post("/v1/chat/completions", json=BODY, headers=HEADERS).status_code == 200


def test_non_stream_and_routing(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "key-1")
    calls = []
    c = _client(calls)
    body = {"model": "deepseek-flash", "temperature": 0.2, "max_tokens": 50,
            "messages": [{"role": "system", "content": "Be brief"}, {"role": "user", "content": "Hi"}]}
    r = c.post("/v1/chat/completions", json=body, headers=HEADERS)
    data = r.json()
    assert calls[0][0] == "generate_with_deepseek"
    assert calls[0][1]["system_instruction"] == "Be brief"
    assert calls[0][1]["prompt"] == "Hi"
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"].startswith("Hello")
    assert data["usage"] == {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}
    c.post("/v1/chat/completions", json=BODY, headers=HEADERS)
    assert calls[1][0] == "generate_with_vertex"


def test_stream(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "key-1")
    r = _client([]).post("/v1/chat/completions", json={**BODY, "stream": True}, headers=HEADERS)
    assert r.headers["content-type"].startswith("text/event-stream")
    lines = [l[6:] for l in r.text.split("\n\n") if l.startswith("data: ")]
    assert lines[-1] == "[DONE]"
    chunks = [json.loads(l) for l in lines[:-1]]
    assert chunks[0]["choices"][0]["delta"]["role"] == "assistant"
    assert "".join(c["choices"][0]["delta"].get("content", "") for c in chunks) == "Hello world, this is a long reply!"
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"


@pytest.mark.parametrize("body,status", [
    ({"model": "gpt-4", "messages": [{"role": "user", "content": "x"}]}, 404),
    ({"model": "gemini-2.5-flash"}, 400),
    ({"messages": [{"role": "user", "content": "x"}]}, 400),
    ({"model": "gemini-2.5-flash", "messages": [{"role": "system", "content": "x"}]}, 400),
])
def test_errors(monkeypatch, body, status):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "key-1")
    assert _client([]).post("/v1/chat/completions", json=body, headers=HEADERS).status_code == status


def test_upstream_failure(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "key-1")
    assert _client([], fail=True).post("/v1/chat/completions", json=BODY, headers=HEADERS).status_code == 500
