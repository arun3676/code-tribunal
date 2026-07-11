"""Shared test fixtures.

By default every test runs fully offline and deterministic: provider keys are
cleared (so the LLM agents fall back to the deterministic engine) and the
coordination backend is forced to the no-op NullBackend (no Band round-trips).
The LLM transport test re-enables specific providers and mocks them with respx.
"""

from __future__ import annotations

import pytest

_PROVIDER_KEYS = (
    "GROQ_API_KEY",
    "CEREBRAS_API_KEY",
    "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY",
    "MERCURY_API_KEY",
    "KIMI_API_KEY",
)


@pytest.fixture(autouse=True)
def offline_env(monkeypatch):
    # Set to empty (not delete) so a stray load_dotenv() in an entrypoint can't
    # repopulate real keys — load_dotenv(override=False) leaves existing vars be.
    for key in _PROVIDER_KEYS:
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("COORDINATION_BACKEND", "null")
    monkeypatch.setenv("BAND_ENABLED", "false")
    monkeypatch.setenv("TRIBUNAL_LLM_PROVIDERS", "groq,cerebras,gemini")
    yield
