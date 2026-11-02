import os
import sys
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

os.environ["DB_DIALECT"] = "sqlite"
os.environ["ENVIRONMENT"] = "development"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402

_RealAsyncClient = httpx.AsyncClient


def _mock_http(monkeypatch, handler):
    transport = httpx.MockTransport(handler)

    def factory(*args, **kwargs):
        kwargs.pop("transport", None)
        return _RealAsyncClient(*args, transport=transport, **kwargs)

    monkeypatch.setattr(server.httpx, "AsyncClient", factory)


def _sse(*chunks: str) -> bytes:
    lines = []
    for c in chunks:
        lines.append('data: {"choices":[{"delta":{"content":%s}}]}\n\n' % server._json.dumps(c))
    lines.append("data: [DONE]\n\n")
    return "".join(lines).encode("utf-8")


def test_local_llm_headers(monkeypatch):
    monkeypatch.setattr(server, "LOCAL_LLM_API_KEY", "")
    assert "Authorization" not in server._local_llm_headers()
    monkeypatch.setattr(server, "LOCAL_LLM_API_KEY", "k123")
    assert server._local_llm_headers()["Authorization"] == "Bearer k123"


def test_local_kb_text_limits_chunks_and_length(monkeypatch):
    monkeypatch.setattr(server, "LOCAL_RAG_CHUNKS", 1)
    monkeypatch.setattr(server, "LOCAL_KB_MAX_CHARS", 20)
    chunks = [SimpleNamespace(content="egy kettő három négy öt hat hét"), SimpleNamespace(content="második")]
    out = server._local_kb_text(chunks)
    assert out.endswith(" …") and "második" not in out and len(out) <= 22
    assert server._local_kb_text([]) == ""


def test_strip_reply_prefixes():
    assert server._strip_reply_prefixes("[2026.10.08 12:00] </div>⁠Szia!") == "Szia!"


@pytest.mark.anyio
async def test_call_local_llm_stream_collects_and_reports(monkeypatch):
    seen = {}

    def handler(request):
        seen["body"] = server._json.loads(request.content)
        return httpx.Response(200, content=_sse("[2026.10.08 12:00] Szia", ", itt ", "vagyok."))

    _mock_http(monkeypatch, handler)
    partials = []
    out = await server._call_local_llm_stream("m", "rendszer", [{"role": "user", "text": "e"}], "most", partials.append)
    assert out == "[2026.10.08 12:00] Szia, itt vagyok."
    assert partials[-1] == "Szia, itt vagyok."
    assert not any(p.startswith("[") for p in partials)
    assert seen["body"]["stream"] is True
    assert [m["role"] for m in seen["body"]["messages"]] == ["system", "user", "user"]


@pytest.mark.anyio
async def test_call_local_llm_stream_errors(monkeypatch):
    _mock_http(monkeypatch, lambda r: httpx.Response(500, content=b"hiba"))
    with pytest.raises(HTTPException):
        await server._call_local_llm_stream("m", "s", [], "u", lambda t: None)

    _mock_http(monkeypatch, lambda r: httpx.Response(200, content=b"data: [DONE]\n\n"))
    with pytest.raises(HTTPException):
        await server._call_local_llm_stream("m", "s", [], "u", lambda t: None)

    _mock_http(monkeypatch, lambda r: httpx.Response(200, content=b'data: {"error":"x"}\n\n'))
    with pytest.raises(HTTPException):
        await server._call_local_llm_stream("m", "s", [], "u", lambda t: None)

    def boom(request):
        raise httpx.ConnectError("nincs kapcsolat", request=request)

    _mock_http(monkeypatch, boom)
    with pytest.raises(HTTPException):
        await server._call_local_llm_stream("m", "s", [], "u", lambda t: None)


@pytest.mark.anyio
async def test_call_llm_uses_selected_local_stream_and_never_falls_back(monkeypatch):
    calls = []

    async def fake_stream(model, sys_prompt, hist, msg, sink):
        calls.append("stream")
        sink("rész")
        return "helyi válasz"

    async def fake_provider(provider, model, api_key, sys_prompt, hist, msg):
        calls.append(provider)
        return "api válasz"

    monkeypatch.setattr(server, "_call_local_llm_stream", fake_stream)
    monkeypatch.setattr(server, "_call_llm_provider", fake_provider)

    got = []
    token = server._chat_stream_sink.set(got.append)
    try:
        assert await server._call_llm("ollama", "qwen", "", "s", [], "u") == "helyi válasz"
        assert calls == ["stream"] and got == ["rész"]

        async def failing_stream(*a, **k):
            raise HTTPException(status_code=502, detail="le")

        monkeypatch.setattr(server, "_call_local_llm_stream", failing_stream)
        got.clear()
        with pytest.raises(HTTPException):
            await server._call_llm("ollama", "qwen", "", "s", [], "u")
        assert calls == ["stream"]
    finally:
        server._chat_stream_sink.reset(token)
