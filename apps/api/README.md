# Code Tribunal API

FastAPI backend for [Code Tribunal](https://github.com/arun3676/code-tribunal). Also ships a
CLI (`tribunal`) and an MCP server (`tribunal-mcp`) over the same engine — see the root README.

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

## CLI

The `tribunal` CLI wraps the same engine for terminals, CI, and coding agents:

```bash
tribunal verify --ticket ticket.md --diff change.diff   # full court (exit 0=APPROVE, 1=BLOCK)
tribunal verify --ticket ticket.md --git --quiet         # diff HEAD; exit-code only, for agent loops
tribunal ghost  --ticket ticket.md --git                 # fast omission pre-check
tribunal drift  --ticket ticket.md --git                 # fast scope-drift pre-check
tribunal init hermes                                      # print the MCP wiring block for an agent
```

`tribunal init <openclaw|hermes|claude|codex|cursor>` emits a ready-to-paste MCP config block
(`--key` bakes in a real `GROQ_API_KEY`; `--write` writes it to the agent's config path without
clobbering an existing file). `--quiet` suppresses human output so agents can rely on the exit code.

## Agent integrations

Wiring config + a Hermes Open Skill for OpenClaw and Hermes live in [`integrations/`](../../integrations/);
the samples there are the verbatim output of `tribunal init` (a test keeps them in sync).

## Package layout

```
code_council/
├── server.py
├── cli.py             # `tribunal` CLI (verify / ghost / drift / init)
├── agent_config.py    # MCP wiring blocks for `tribunal init` (single source of truth)
├── mcp_server.py      # `tribunal-mcp` MCP server
├── analyzer.py
├── scanners/
├── multimodal.py
├── github.py          # reserved — not exposed via API yet
└── tribunal/
    ├── protocol.py      # Pydantic schemas + AGENTS roster
    ├── fixtures.py      # auth-login-001, health-check-002, payment-refund-003, user-profile-004
    ├── llm.py           # reasoning layer: Groq → Cerebras → Gemini fallback
    ├── runner.py        # staged trial: LLM agents + deterministic fallback
    ├── coordination.py  # CoordinationBackend seam (Band today, swappable)
    └── band_adapter.py
```

## Tribunal env vars

See [`apps/api/.env.example`](.env.example) — `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GEMINI_API_KEY`,
`TRIBUNAL_LLM_PROVIDERS`, `COORDINATION_BACKEND`, and `BAND_*` (coordination layer).

## Deploy

Railway — see root [`DEPLOYMENT.md`](../../DEPLOYMENT.md).
