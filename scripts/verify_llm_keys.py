"""Smoke-test configured LLM API keys (never prints secrets)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "apps" / "api" / ".env", override=False)


def status(label: str, ok: bool, detail: str = "") -> None:
    mark = "OK" if ok else "FAIL"
    msg = f"[{mark}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def test_gemini(key: str) -> None:
    if not key:
        status("Gemini", False, "key missing")
        return
    try:
        import google.generativeai as genai

        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        resp = model.generate_content("Reply with exactly: pong")
        text = (resp.text or "").strip()
        status("Gemini", "pong" in text.lower(), text[:80] or "empty response")
    except Exception as exc:
        status("Gemini", False, str(exc)[:120])


def test_openai_compat(label: str, key: str, base_url: str, model: str) -> None:
    if not key:
        status(label, False, "key missing")
        return
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: pong"}],
            max_tokens=8,
        )
        text = (resp.choices[0].message.content or "").strip()
        status(label, "pong" in text.lower(), text[:80] or "empty response")
    except Exception as exc:
        status(label, False, str(exc)[:120])


def main() -> int:
    print("=== LLM key smoke tests ===")
    test_gemini(os.getenv("GEMINI_API_KEY", "").strip())
    test_openai_compat(
        "DeepSeek",
        os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "https://api.deepseek.com",
        "deepseek-chat",
    )
    test_openai_compat(
        "Mercury",
        os.getenv("MERCURY_API_KEY", "").strip(),
        "https://api.inceptionlabs.ai/v1",
        "mercury-coder-small",
    )
    test_openai_compat(
        "Kimi",
        os.getenv("Kimi_API_KEY", "").strip(),
        "https://api.moonshot.ai/v1",
        "moonshot-v1-8k",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
