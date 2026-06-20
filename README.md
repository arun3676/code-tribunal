# Code Tribunal

**Did the AI build what you actually asked for?**

Code Tribunal is an intent-conformance review engine for AI-generated code. Instead of asking one model whether a diff looks correct, Tribunal reconciles the **original ticket** against the **actual implementation** and returns a merge verdict, a 0–100 trust score, and a traceability ledger.

It ships three ways:

- **CLI** — `tribunal verify` in any terminal or CI pipeline.
- **MCP server** — drop it into Claude Code, Codex, or Cursor so your coding agent can self-check a diff before a human ever sees it.
- **Web demo** — a live War Room that shows the agents deliberating.

A CLERK agent opens the case. ADVOCATE extracts requirements. SURVEYOR inspects the diff. GHOST finds requested work that is missing. DRIFT finds unrequested scope changes. WARDEN is recruited for security-sensitive changes. ARBITER produces the verdict.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Problem

AI coding agents produce large diffs quickly. Standard PR review asks *"is this code correct?"* Tribunal asks *"did the AI build what you actually asked for?"* — reconciling the ticket/spec against the diff before merge.

## How Tribunal works

1. Load a **docket** (ticket + diff + touched files/domains).
2. **CLERK** opens the room and routes `@mention` handoffs.
3. **ADVOCATE** extracts requirements; **SURVEYOR** inspects implementation.
4. **GHOST** finds **negative space** (requested but missing work).
5. **DRIFT** finds **scope creep** (unauthorized changes).
6. **WARDEN** is recruited mid-trial when auth/security is touched.
7. **ARBITER** issues verdict, trust score (0–100), merge decision, and traceability ledger.

## Architecture

Three decoupled layers — swapping any one never touches the others:

- **Reasoning** — the agents think on free, open models (Groq → Cerebras → Gemini fallback chain). Bring your own API keys; the chain skips any provider you haven't configured and falls back to deterministic logic if none are set.
- **Coordination** — Band runs the room (rooms, participants, `@mention` handoffs, structured events, mid-trial recruitment).
- **Scoring** — the trust score and traceability ledger are computed by deterministic, explainable math.

## Agent roster

| Agent | Role | Reasoning | Coordination |
|-------|------|-----------|--------------|
| CLERK | Orchestrator | — | Band |
| ADVOCATE | Intent witness | Groq | Band |
| SURVEYOR | Implementation witness | Groq | Band |
| GHOST | Omission auditor | Groq | Band |
| DRIFT | Scope auditor | Cerebras | Band |
| WARDEN | Security witness | Groq | Band (recruited) |
| ARBITER | Judge | Groq + deterministic scoring | Band |

## Install (CLI / MCP)

Run the MCP server with no clone via [`uvx`](https://docs.astral.sh/uv/). Bring your own key in the `env` block.

**Claude Code / Cursor** (`mcpServers` config):

```jsonc
{
  "mcpServers": {
    "tribunal": {
      "command": "uvx",
      "args": ["--from", "code-tribunal", "tribunal-mcp"],
      "env": { "GROQ_API_KEY": "your-key-here" }
    }
  }
}
```

**Codex** (`~/.codex/config.toml`):

```toml
[mcp_servers.tribunal]
command = "uvx"
args = ["--from", "code-tribunal", "tribunal-mcp"]
env = { GROQ_API_KEY = "your-key-here" }
```

(Or `codex mcp add` to register it interactively.)

**CLI** — gate a PR in CI (exit code `0` = APPROVE, `1` = BLOCK):

```bash
tribunal verify --ticket ticket.md --diff change.diff
```

MCP tools exposed: `verify_intent_conformance` (full court), `ghost_check` (fast omission pre-check), `drift_check` (fast scope-drift pre-check).

## Band coordination

Tribunal uses Band as the active coordination layer:

- CLERK creates a Band room.
- Agents are recruited as participants.
- Directed `@mention` messages trigger handoffs.
- Structured Events record requirements, findings, omissions, drift, constraints, and verdicts.
- WARDEN is recruited mid-trial when security-sensitive code is detected.

Set `BAND_ENABLED=true`, `BAND_STRICT=true`, and agent UUIDs for live mirroring. Run `python scripts/verify_band_trial.py` before deploy.

## Demo cases

**auth-login-001** (hero case):

- Ticket requests secure login: endpoint, bcrypt, rate limiting, audit log, tests, no auth middleware change.
- Diff implements login + bcrypt + audit + tests but **omits rate limiting** (GHOST / R3).
- Diff **changes auth middleware** without authorization (DRIFT).
- WARDEN recruited → **DOES_NOT_CONFORM**, Trust Score ~35/100, **BLOCK**.

**health-check-002** — clean pass case. **payment-refund-003** — heavy BLOCK. **user-profile-004** — clean APPROVE.

## Local run (web demo)

```bash
git clone <your-repo-url> code-tribunal
cd code-tribunal
cp .env.example .env    # add LLM (Groq/Cerebras/Gemini) + Band keys
python scripts/check_env_keys.py
python scripts/verify_band_trial.py   # Band smoke test
docker compose up --build
```

Open [http://localhost:3000/tribunal](http://localhost:3000/tribunal) · API [http://localhost:8000/health](http://localhost:8000/health)

```bash
curl -N -X POST http://localhost:8000/tribunal/run \
  -H "Content-Type: application/json" \
  -d '{"fixture_id":"auth-login-001"}'
```

## Other modes (web demo)

| Mode | Route | Description |
|------|-------|-------------|
| Solo | `/` | Single-model code analysis |
| Council | `/` | Multi-model consensus |
| Static scan | `/` | Security + performance rules |
| Multimodal | `/` | Vision model upload |

## Deployment

- **API:** `apps/api` on Railway — see [`DEPLOYMENT.md`](DEPLOYMENT.md)
- **Web:** `apps/web` on Vercel — set `NEXT_PUBLIC_API_URL`

## License

MIT — see [LICENSE](LICENSE).
