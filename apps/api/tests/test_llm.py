"""Transport tests for the LLM provider fallback chain (respx-mocked)."""

from __future__ import annotations

import httpx
import respx

from code_council.tribunal import llm

_SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
    "additionalProperties": False,
}

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"


def _completion(content: str, model: str = "llama-3.3-70b-versatile") -> dict:
    return {
        "id": "cmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def test_groq_returns_parsed_json(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("TRIBUNAL_LLM_PROVIDERS", "groq,cerebras")
    with respx.mock(assert_all_called=False) as mock:
        mock.post(_GROQ_URL).mock(return_value=httpx.Response(200, json=_completion('{"ok": true}')))
        result = llm.complete_json("sys", "user", _SCHEMA)
    assert result == {"ok": True}


def test_falls_through_to_cerebras_when_groq_fails(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("CEREBRAS_API_KEY", "test-cerebras")
    monkeypatch.setenv("TRIBUNAL_LLM_PROVIDERS", "groq,cerebras")
    with respx.mock(assert_all_called=False) as mock:
        mock.post(_GROQ_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))
        mock.post(_CEREBRAS_URL).mock(
            return_value=httpx.Response(200, json=_completion('{"ok": true}', model="llama-3.3-70b"))
        )
        result = llm.complete_json("sys", "user", _SCHEMA)
    assert result == {"ok": True}


def test_returns_none_when_no_provider_configured():
    # offline_env autouse fixture has cleared every provider key.
    assert llm.available_providers() == []
    assert llm.complete_json("sys", "user", _SCHEMA) is None
