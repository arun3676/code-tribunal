# Contributing to Code Tribunal

Thanks for your interest! Issues and PRs are welcome.

## Repo layout

- `apps/api` — Python package (`code-tribunal`): the delivery surfaces
  (`server.py`, `cli.py`, `mcp_server.py`) over two independent engines —
  `code_council/tribunal/` (the intent-conformance court) and
  `code_council/council/` (the older multi-model analysis engine). They share no
  code; only the FastAPI server mounts both.
- `apps/web` — Next.js landing page + War Room demo.
- `integrations/` — MCP wiring guides for coding agents (kept in sync with
  `tribunal init` — see `apps/api/tests/test_init.py`).
- `scripts/` — operational smoke tests (key checks, Band trial, Railway env).

## Dev setup

```bash
# API (Python 3.11+)
cd apps/api
pip install -e .[dev]
python -m pytest -q          # offline + deterministic; no API keys needed
python -m ruff check .

# Web (Node 22 + pnpm)
cd apps/web
pnpm install
pnpm dev                     # http://localhost:3000
pnpm lint && pnpm typecheck
```

Copy `.env.example` to `.env` for keys — everything degrades gracefully when
keys are missing (the engine falls back to deterministic logic).

## Ground rules

- The test suite must run **offline**: provider keys are cleared in
  `tests/conftest.py`, and the four demo fixtures in
  `code_council/tribunal/fixtures.py` are pinned `engine="deterministic"` —
  their verdicts must stay byte-stable (`tests/test_fixtures.py`).
- Trust-score math lives in `runner.py adjudicate()` and is deterministic by
  design; LLM output may enrich prose but never the score.
- New LLM providers go in `code_council/tribunal/llm.py` (fallback chain).
- Run `ruff check`, `pytest`, `pnpm lint`, and `pnpm typecheck` before pushing —
  CI enforces all four.

## Releases

Bump `version` in `apps/api/pyproject.toml` **and** `code_council/__init__.py`
(a test asserts they match), add a `CHANGELOG.md` entry, tag `vX.Y.Z`, and
publish a GitHub Release — `publish.yml` pushes to PyPI via trusted publishing.
