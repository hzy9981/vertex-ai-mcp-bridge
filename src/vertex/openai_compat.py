"""OpenAI-compatible /v1/chat/completions handler."""

import hmac
import json
import os
import re
import time
import uuid

from starlette.responses import JSONResponse, StreamingResponse

API_KEY_ENV = "OPENAI_COMPATIBLE_API_KEY"
STREAM_CHUNK_SIZE = 20


def _error(status: int, message: str, err_type: str, code: str | None = None):
    return JSONResponse(
        {"error": {"message": message, "type": err_type, "code": code}},
        status_code=status,
    )


def _allowed_keys() -> list[str]:
    raw = os.environ.get(API_KEY_ENV, "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def _authorized(request, keys: list[str]) -> bool:
    header = request.headers.get("authorization", "")
    match = re.match(r"^Bearer\s+(.+)$", header.strip(), re.IGNORECASE)
    if not match:
        return False
    token = match.group(1).strip().encode()
    return any(hmac.compare_digest(token, k.encode()) for k in keys)


def _content_text(content) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and p.get("type", "text") == "text":
                parts.append(str(p.get("text", "")))
        return "".join(parts)
    return None


def _convert_messages(messages) -> tuple[str, str | None]:
    """Convert OpenAI messages to (prompt, system_instruction)."""
    system, turns = [], []
    for m in messages:
        if not isinstance(m, dict) or not isinstance(m.get("role"), str):
            raise ValueError("each message must be an object with a 'role'")
        text = _content_text(m.get("content"))
        if text is None:
            raise ValueError("each message must have string or text-part 'content'")
        if m["role"] in ("system", "developer"):
            system.append(text)
        else:
            turns.append((m["role"], text))
    if not turns:
        raise ValueError("'messages' must contain at least one non-system message")
    if len(turns) == 1 and turns[0][0] == "user":
        prompt = turns[0][1]
    else:
        prompt = "\n\n".join(f"{role}: {text}" for role, text in turns)
    return prompt, ("\n\n".join(system) or None)


def _normalize_result(result) -> dict:
    """Normalize the various shapes returned by mcp.call_tool into a dict."""
    if isinstance(result, tuple) and len(result) == 2:
        content, structured = result
        if isinstance(structured, dict):
            return structured.get("result", structured) if set(structured) == {"result"} else structured
        result = content
    if isinstance(result, dict):
        return result
    if isinstance(result, (list, tuple)):
        for item in result:
            text = getattr(item, "text", None)
            if text is not None:
                return json.loads(text)
    raise RuntimeError("Unexpected tool result format")


def _chunk(cid, created, model, delta, finish_reason=None) -> str:
    payload = {
        "id": cid,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _finish_reason(raw) -> str:
    raw = str(raw or "stop").lower()
    if "length" in raw or "max_tokens" in raw:
        return "length"
    return "stop"


async def handle_chat_completions(request, call_tool):
    """Handle POST /v1/chat/completions. `call_tool(name, args)` runs an MCP tool."""
    keys = _allowed_keys()
    if not keys:
        return _error(
            501,
            f"OpenAI-compatible API is disabled ({API_KEY_ENV} is not set)",
            "not_implemented",
            "disabled",
        )
    if not _authorized(request, keys):
        return _error(401, "Invalid or missing API key", "authentication_error", "invalid_api_key")

    try:
        body = await request.json()
    except Exception:
        return _error(400, "Request body must be valid JSON", "invalid_request_error")
    if not isinstance(body, dict):
        return _error(400, "Request body must be a JSON object", "invalid_request_error")

    model = body.get("model")
    messages = body.get("messages")
    if not isinstance(model, str) or not model:
        return _error(400, "'model' is required", "invalid_request_error")
    if not isinstance(messages, list) or not messages:
        return _error(400, "'messages' must be a non-empty array", "invalid_request_error")

    if model.startswith("gemini-"):
        tool = "generate_with_vertex"
    elif model.startswith("deepseek-"):
        tool = "generate_with_deepseek"
    else:
        return _error(404, f"The model '{model}' does not exist", "invalid_request_error", "model_not_found")

    try:
        prompt, system = _convert_messages(messages)
        args: dict = {"prompt": prompt, "model": model}
        for src, dst, typ in (
            ("temperature", "temperature", (int, float)),
            ("max_tokens", "max_tokens", int),
            ("top_p", "top_p", (int, float)),
        ):
            val = body.get(src)
            if val is not None:
                if isinstance(val, bool) or not isinstance(val, typ):
                    raise ValueError(f"'{src}' has an invalid type")
                args[dst] = val
        if system:
            args["system_instruction"] = system
    except ValueError as e:
        return _error(400, str(e), "invalid_request_error")
    stream = body.get("stream", False)
    if not isinstance(stream, bool):
        return _error(400, "'stream' must be a boolean", "invalid_request_error")

    try:
        result = _normalize_result(await call_tool(tool, args))
        text = result.get("text", "")
    except Exception as e:
        return _error(500, f"Upstream error: {e}", "server_error")

    cid = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    finish = _finish_reason(result.get("finish_reason"))

    if stream:

        async def events():
            first = True
            for i in range(0, len(text), STREAM_CHUNK_SIZE):
                delta = {"content": text[i : i + STREAM_CHUNK_SIZE]}
                if first:
                    delta["role"] = "assistant"
                    first = False
                yield _chunk(cid, created, model, delta)
            if first:
                yield _chunk(cid, created, model, {"role": "assistant", "content": ""})
            yield _chunk(cid, created, model, {}, finish)
            yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    prompt_tokens = int(result.get("input_tokens", 0) or 0)
    completion_tokens = int(result.get("output_tokens", 0) or 0)
    return JSONResponse(
        {
            "id": cid,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": finish,
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
    )
