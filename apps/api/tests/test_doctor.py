"""`tribunal doctor` — BYO-key health check (respx-mocked, fully offline)."""

from __future__ import annotations

import json

import httpx
import respx

from code_council import cli

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"

_SECRET = "gsk-super-secret-key-do-not-print"


def _completion(model: str = "llama-3.3-70b-versatile") -> dict:
    return {
        "id": "cmpl-doctor",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": "pong"}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def test_doctor_no_keys_exits_1(capsys):
    # offline_env autouse fixture has cleared every provider key.
    assert cli.main(["doctor"]) == 1
    out = capsys.readouterr().out
    assert out.count("KEY MISSING") == 3  # groq, cerebras, gemini
    assert "NOT READY" in out


def test_doctor_offline_key_present_exits_0(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", _SECRET)
    assert cli.main(["doctor", "--offline"]) == 0
    captured = capsys.readouterr()
    assert "KEY SET" in captured.out
    assert "KEY MISSING" in captured.out  # cerebras + gemini still unset
    assert _SECRET not in captured.out + captured.err


def test_doctor_offline_no_keys_exits_1(capsys):
    assert cli.main(["doctor", "--offline"]) == 1
    assert "KEY MISSING" in capsys.readouterr().out


def test_doctor_live_pass_exits_0(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", _SECRET)
    monkeypatch.setenv("GROQ_MODEL", "doctor-test-model")
    monkeypatch.setenv("TRIBUNAL_LLM_PROVIDERS", "groq")
    with respx.mock(assert_all_called=True) as mock:
        mock.post(_GROQ_URL).mock(return_value=httpx.Response(200, json=_completion()))
        assert cli.main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "doctor-test-model" in captured.out  # reports the model used
    assert _SECRET not in captured.out + captured.err


def test_doctor_live_fail_exits_1(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", _SECRET)
    monkeypatch.setenv("TRIBUNAL_LLM_PROVIDERS", "groq")
    with respx.mock(assert_all_called=True) as mock:
        mock.post(_GROQ_URL).mock(
            return_value=httpx.Response(401, json={"error": {"message": "invalid api key"}})
        )
        assert cli.main(["doctor"]) == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert _SECRET not in captured.out + captured.err


def test_doctor_mixed_chain_one_pass_is_enough(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", _SECRET)
    monkeypatch.setenv("CEREBRAS_API_KEY", "csk-another-secret")
    monkeypatch.setenv("TRIBUNAL_LLM_PROVIDERS", "groq,cerebras")
    with respx.mock(assert_all_called=True) as mock:
        mock.post(_GROQ_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))
        mock.post(_CEREBRAS_URL).mock(return_value=httpx.Response(200, json=_completion("zai-glm-4.7")))
        assert cli.main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "FAIL" in captured.out and "PASS" in captured.out
    assert _SECRET not in captured.out + captured.err
    assert "csk-another-secret" not in captured.out + captured.err


def test_doctor_json_output(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", _SECRET)
    monkeypatch.setenv("TRIBUNAL_LLM_PROVIDERS", "groq")
    with respx.mock(assert_all_called=True) as mock:
        mock.post(_GROQ_URL).mock(return_value=httpx.Response(200, json=_completion()))
        assert cli.main(["doctor", "--json"]) == 0
    raw = capsys.readouterr().out
    assert _SECRET not in raw
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["offline"] is False
    (row,) = data["providers"]
    assert row["provider"] == "groq"
    assert row["status"] == "PASS"
    assert row["key_present"] is True
    assert row["model"]


def test_doctor_json_no_keys(capsys):
    assert cli.main(["doctor", "--json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert all(row["status"] == "MISSING" for row in data["providers"])
    assert [row["provider"] for row in data["providers"]] == ["groq", "cerebras", "gemini"]
