"""Verify Band coordination + LLM reasoning keys without printing secrets."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "apps" / "api" / ".env", override=False)


def pick(*names: str) -> str:
    for name in names:
        val = os.getenv(name, "").strip()
        if val:
            return val
    return ""


def ok(label: str, passed: bool, detail: str = "") -> None:
    mark = "OK" if passed else "FAIL"
    line = f"[{mark}] {label}"
    if detail:
        line += f" — {detail}"
    print(line)


def test_band() -> None:
    key = pick("BAND_API_KEY")
    base = pick("BAND_BASE_URL") or "https://app.band.ai/api/v1"
    enabled = os.getenv("BAND_ENABLED", "").lower() == "true"
    ok("BAND_ENABLED=true", enabled, "set BAND_ENABLED=true for live mode")
    if not key:
        ok("Band CLERK key", False, "BAND_API_KEY missing")
        return
    ids = {
        "CLERK": pick("BAND_CLERK_ID"),
        "ADVOCATE": pick("BAND_ADVOCATE_ID"),
        "SURVEYOR": pick("BAND_SURVEYOR_ID"),
        "GHOST": pick("BAND_GHOST_ID"),
        "DRIFT": pick("BAND_DRIFT_ID"),
        "WARDEN": pick("BAND_WARDEN_ID"),
        "ARBITER": pick("BAND_ARBITER_ID"),
    }
    missing = [name for name, val in ids.items() if not val]
    ok("Band agent UUIDs (7)", not missing, f"missing: {missing}" if missing else "all set")
    try:
        resp = httpx.get(
            f"{base.rstrip('/')}/agent/me",
            headers={"X-API-Key": key},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            name = data.get("name") or data.get("agent", {}).get("name") or "connected"
            ok("Band GET /agent/me", True, f"agent: {name}")
        else:
            ok("Band GET /agent/me", False, f"HTTP {resp.status_code}")
    except Exception as exc:
        ok("Band GET /agent/me", False, str(exc)[:100])


def test_openai_compat(label: str, key: str, base_url: str, model: str) -> None:
    if not key:
        ok(label, False, "key missing")
        return
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: pong"}],
            max_tokens=16,
        )
        text = (resp.choices[0].message.content or "").strip()
        ok(label, bool(text), text[:60] or "empty response")
    except Exception as exc:
        ok(label, False, str(exc)[:120])


def main() -> int:
    print("=== API key verification ===\n")
    test_band()
    print()
    test_openai_compat(
        "Groq",
        pick("GROQ_API_KEY", "groq_api_key"),
        "https://api.groq.com/openai/v1",
        "llama-3.3-70b-versatile",
    )
    test_openai_compat(
        "Cerebras",
        pick("CEREBRAS_API_KEY", "cerebras_api_key"),
        "https://api.cerebras.ai/v1",
        "llama-3.3-70b",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
