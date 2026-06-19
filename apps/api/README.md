# Code Council API

FastAPI backend for [Code Council Tribunal](https://github.com/arun3676/code-tribunal-lab-lab).

## Endpoints

| Method | Path | Type | Description |
|--------|------|------|-------------|
| GET | `/health` | JSON | Health check |
| GET | `/models` | JSON | Available LLM providers |
| POST | `/analyze` | SSE | Single-model streaming analysis |
| POST | `/council` | SSE | Multi-model council |
| POST | `/scan` | JSON | Static security + performance scan |
| POST | `/multimodal` | JSON | Image analysis |
| GET | `/tribunal/fixtures` | JSON | Demo docket list |
| POST | `/tribunal/run` | SSE | Stream a Tribunal trial |

### Tribunal run payload

```json
{ "fixture_id": "auth-login-001" }
```

Or ad-hoc:

```json
{ "title": "...", "ticket": "...", "diff": "...", "touched_domains": ["auth"] }
```

### Tribunal SSE events

`phase` · `message` · `event` · `recruitment` · `verdict` · `done` · `error`

## Local run

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -e .
cp .env.example .env
uvicorn code_council.server:app --reload --port 8000
```

Or from repo root: `docker compose up api`

## Package layout

```
code_council/
├── server.py
├── analyzer.py
├── scanners/
├── multimodal.py
├── github.py          # reserved — not exposed via API yet
└── tribunal/
    ├── protocol.py    # Pydantic schemas + AGENTS roster
    ├── fixtures.py    # auth-login-001, health-check-002
    ├── runner.py      # deterministic staged trial
    └── band_adapter.py
```

## Tribunal env vars

See [`apps/api/.env.example`](.env.example) — `BAND_*`, `AIMLAPI_API_KEY`, `FEATHERLESS_API_KEY`.

## Deploy

Railway — see root [`DEPLOYMENT.md`](../../DEPLOYMENT.md).
