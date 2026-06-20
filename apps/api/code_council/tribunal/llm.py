"""Reasoning layer for the Tribunal agents.

A small provider-fallback chain that returns structured JSON. The Tribunal
agents (ADVOCATE, SURVEYOR, GHOST, DRIFT, ARBITER) call :func:`complete_json`
to reason over arbitrary tickets/diffs; when no provider is configured or every
provider fails, it returns ``None`` so the caller can fall back to the
deterministic logic in ``runner.py``.

Providers are all OpenAI-compatible (Groq, Cerebras) plus Gemini, swapping the
``base_url`` exactly like ``analyzer.py`` does. Keys are read from the process
environment only (env-based BYO): set ``GROQ_API_KEY`` / ``CEREBRAS_API_KEY`` /
``GEMINI_API_KEY``. Chain order comes from ``TRIBUNAL_LLM_PROVIDERS``.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from openai import OpenAI

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None

logger = logging.getLogger("code_council.tribunal.llm")

# Per-call wall-clock budget (seconds). Kept short so a slow/unavailable
# provider hands off to the next one quickly.
TIMEOUT = 30.0

DEFAULT_CHAIN = "groq,cerebras,gemini"

# provider -> (api key env var, base url, model env var, default model)
_OPENAI_COMPATIBLE: dict[str, tuple[str, str, str, str]] = {
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1", "GROQ_MODEL", "llama-3.3-70b-versatile"),
    "cerebras": ("CEREBRAS_API_KEY", "https://api.cerebras.ai/v1", "CEREBRAS_MODEL", "llama-3.3-70b"),
}

_KEY_ENV: dict[str, str] = {
    "groq": "GROQ_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def resolve_key(provider: str) -> str:
    """Return the configured API key for ``provider`` from the process env.

    Env-based only (BYO): each user supplies their own key via the environment
    or their MCP/CLI client config. Returns an empty string when unset.
    """

    env_var = _KEY_ENV.get(provider, "")
    return os.getenv(env_var, "").strip() if env_var else ""


def _chain() -> list[str]:
    raw = os.getenv("TRIBUNAL_LLM_PROVIDERS", DEFAULT_CHAIN)
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def available_providers() -> list[str]:
    """Chain entries whose API key is present — handy for health/tests."""

    return [provider for provider in _chain() if resolve_key(provider)]


def _extract_json(content: str) -> dict | None:
    """Parse a JSON object from raw model output, tolerating markdown fences."""

    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def _call_openai_compatible(provider: str, system: str, user: str, schema: dict, max_tokens: int) -> dict | None:
    api_key_env, base_url, model_env, default_model = _OPENAI_COMPATIBLE[provider]
    client = OpenAI(api_key=resolve_key(provider), base_url=base_url, timeout=TIMEOUT)
    model = os.getenv(model_env, default_model)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    json_schema_format: dict[str, Any] = {
        "type": "json_schema",
        "json_schema": {"name": "result", "schema": schema, "strict": True},
    }
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.1,
            max_tokens=max_tokens,
            response_format=json_schema_format,  # type: ignore[arg-type]
        )
    except Exception as exc:
        # Cerebras (and some models) may reject strict json_schema — retry once
        # with the looser json_object mode before giving up on this provider.
        logger.warning("%s json_schema call failed (%s); retrying as json_object", provider, exc)
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.1,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
    content = (response.choices[0].message.content or "").strip()
    return _extract_json(content)


# Schema keys Gemini's response_schema dialect rejects (it only speaks a subset
# of OpenAPI/JSON-Schema). Strip them recursively before handing a schema over.
_GEMINI_UNSUPPORTED_KEYS = frozenset(
    {"additionalProperties", "strict", "$schema", "title", "default", "examples", "$id"}
)


def _gemini_schema(schema: Any) -> Any:
    """Deep-copy ``schema`` with keys Gemini can't parse removed."""

    if isinstance(schema, dict):
        return {
            key: _gemini_schema(value)
            for key, value in schema.items()
            if key not in _GEMINI_UNSUPPORTED_KEYS
        }
    if isinstance(schema, list):
        return [_gemini_schema(item) for item in schema]
    return schema


def _call_gemini(system: str, user: str, schema: dict, max_tokens: int) -> dict | None:
    if genai is None:
        raise RuntimeError("google-generativeai is not installed")
    genai.configure(api_key=resolve_key("gemini"))
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = f"{system}\n\n{user}"
    base_config: dict[str, Any] = {
        "response_mime_type": "application/json",
        "max_output_tokens": max_tokens,
        "temperature": 0.1,
    }
    model = genai.GenerativeModel(model_name, system_instruction=system)
    try:
        response = model.generate_content(
            user,
            generation_config={**base_config, "response_schema": _gemini_schema(schema)},
        )
    except Exception as exc:
        # Some schemas aren't expressible in Gemini's response_schema dialect —
        # fall back to plain JSON mime type and parse from text.
        logger.warning("Gemini response_schema call failed (%s); retrying without schema", exc)
        response = model.generate_content(prompt, generation_config=base_config)
    text = getattr(response, "text", None) or ""
    return _extract_json(text.strip())


def complete_json(
    system: str,
    user: str,
    schema: dict,
    *,
    max_tokens: int = 1024,
    provider_hint: str | None = None,
) -> dict | None:
    """Return a JSON object from the first available provider in the chain.

    Walks the configured provider chain (``TRIBUNAL_LLM_PROVIDERS``); for each
    provider with a key present, attempts a structured-JSON completion. Returns
    the first parsed dict, or ``None`` if every provider is unconfigured or
    fails — signalling the caller to use its deterministic fallback.

    Args:
        system: System prompt (role / instructions).
        user: User prompt (the ticket/diff/context to reason over).
        schema: JSON Schema the response must conform to.
        max_tokens: Output token budget.
        provider_hint: Optional provider name to try first (e.g. "cerebras"
            for DRIFT), before the rest of the chain.
    """

    order = _chain()
    if provider_hint:
        hint = provider_hint.strip().lower()
        order = [hint] + [p for p in order if p != hint]

    attempted = False
    for provider in order:
        if not resolve_key(provider):
            continue
        attempted = True
        try:
            if provider in _OPENAI_COMPATIBLE:
                result = _call_openai_compatible(provider, system, user, schema, max_tokens)
            elif provider == "gemini":
                result = _call_gemini(system, user, schema, max_tokens)
            else:
                logger.warning("Unknown LLM provider in chain: %s", provider)
                continue
            if result is not None:
                logger.info("Tribunal LLM call served by %s", provider)
                return result
            logger.warning("%s returned unparseable JSON; trying next provider", provider)
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("%s call failed: %s", provider, exc)

    if not attempted:
        logger.info("No LLM provider configured; using deterministic fallback")
    return None
