# Code Tribunal API

FastAPI backend for [Code Tribunal](https://github.com/arun3676/code-tribunal). Also ships a
CLI (`tribunal`) and an MCP server (`tribunal-mcp`) over the same engine — see the
[root README](https://github.com/arun3676/code-tribunal#readme) and the
[live demo](https://code-council.vercel.app). Published on PyPI as
[`code-tribunal`](https://pypi.org/project/code-tribunal/):

```bash
uvx --from code-tribunal tribunal --help       # CLI, no install
uvx --from code-tribunal tribunal-mcp          # MCP server, no install
```

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
| POST | `/tribunal/verdict` | JSON | One-shot trial → verdict (headless; 15–30s) |
| POST | `/tribunal/review-pr` | JSON | Adjudicate a GitHub PR by URL |
| POST | `/waitlist` | JSON | Hosted-court invite registration |
| POST | `/webhooks/github` | JSON | GitHub webhook (HMAC-verified) |

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
tribunal doctor                                           # check that your BYO provider keys work
```

`tribunal init <openclaw|hermes|claude|codex|cursor>` emits a ready-to-paste MCP config block.
Bake in real keys with `--key`/`--groq-key`, `--cerebras-key`, `--gemini-key`; set the fallback
chain with `--providers groq,cerebras,gemini`; override models with `--groq-model` /
`--cerebras-model` / `--gemini-model`. `--write` writes the block to the agent's config path
without clobbering an existing file. `--quiet` suppresses human output so agents can rely on
the exit code.

`tribunal doctor [--json] [--offline]` is the recommended first step after adding keys: it
prints KEY SET/MISSING per provider plus a live 1-token PASS/FAIL (keys are never printed) and
exits `0` if at least one provider works.

## Models (bring your own free keys)

Any one key is enough — the chain skips providers without keys, and with zero keys the
deterministic engine still runs. Free keys: [console.groq.com](https://console.groq.com),
[cloud.cerebras.ai](https://cloud.cerebras.ai), [aistudio.google.com](https://aistudio.google.com).

| Provider | Models | Override env |
|----------|--------|--------------|
| Groq (default) | `llama-3.3-70b-versatile` (default) · `openai/gpt-oss-120b` · `meta-llama/llama-4-scout-17b-16e-instruct` (Llama 4 Scout) | `GROQ_MODEL` |
| Cerebras | `zai-glm-4.7` | `CEREBRAS_MODEL` |
| Gemini | `gemini-3.5-flash` | `GEMINI_MODEL` |

Fallback chain order: `TRIBUNAL_LLM_PROVIDERS=groq,cerebras,gemini`.

## Agent integrations

Wiring config + a Hermes Open Skill for OpenClaw and Hermes live in
[`integrations/`](https://github.com/arun3676/code-tribunal/tree/main/integrations);
the samples there are the verbatim output of `tribunal init` (a test keeps them in sync).

## Package layout

```
code_council/
├── server.py
├── cli.py             # `tribunal` CLI (verify / ghost / drift / init / doctor)
├── agent_config.py    # MCP wiring blocks for `tribunal init` (single source of truth)
├── mcp_server.py      # `tribunal-mcp` MCP server
├── analyzer.py
├── scanners/
├── multimodal.py
├── github.py          # GitHub diff fetching (powers /tribunal/review-pr + webhook)
└── tribunal/
    ├── protocol.py      # Pydantic schemas + AGENTS roster
    ├── fixtures.py      # auth-login-001, health-check-002, payment-refund-003, user-profile-004
    ├── llm.py           # reasoning layer: Groq → Cerebras → Gemini fallback
    ├── runner.py        # staged trial: LLM agents + deterministic fallback
    ├── coordination.py  # CoordinationBackend seam (Band today, swappable)
    └── band_adapter.py
```

## Tribunal env vars

See [`apps/api/.env.example`](https://github.com/arun3676/code-tribunal/blob/main/apps/api/.env.example) —
`GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GEMINI_API_KEY`, `TRIBUNAL_LLM_PROVIDERS`,
`GROQ_MODEL` / `CEREBRAS_MODEL` / `GEMINI_MODEL` (optional overrides),
`COORDINATION_BACKEND`, and `BAND_*` (coordination layer).

## Deploy

Railway — see [`DEPLOYMENT.md`](https://github.com/arun3676/code-tribunal/blob/main/DEPLOYMENT.md).
