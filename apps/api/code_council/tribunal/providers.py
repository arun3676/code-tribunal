"""Optional LLM providers for Tribunal agent enrichment."""

from __future__ import annotations

import json
import logging
import os
import re

import httpx

logger = logging.getLogger("code_council.tribunal.providers")

FEATHERLESS_BASE = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1").rstrip("/")
FEATHERLESS_MODEL = os.getenv("FEATHERLESS_MODEL", "meta-llama/Llama-3.1-8B-Instruct")


def call_featherless_json(prompt: str) -> dict | None:
    """Call Featherless OpenAI-compatible chat completions; return parsed JSON or None."""

    api_key = os.getenv("FEATHERLESS_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{FEATHERLESS_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": FEATHERLESS_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Respond with a single JSON object: {\"explanation\": \"...\"}. No markdown.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 300,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"explanation": content.strip()}
    except Exception as exc:  # pragma: no cover - network path
        logger.warning("Featherless call failed: %s", exc)
        return None
