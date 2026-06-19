# Code Council Tribunal

**Did the AI build what you actually asked for?**

Code Council Tribunal is a Band-powered intent-conformance review room for AI-generated code. Instead of asking one model whether a diff looks correct, Tribunal compares the original ticket against the actual implementation.

A CLERK agent opens the case in Band. ADVOCATE extracts requirements. SURVEYOR inspects the diff. GHOST finds requested work that is missing. DRIFT finds unrequested scope changes. WARDEN is recruited for security-sensitive changes. ARBITER produces the merge verdict, trust score, and traceability ledger.

**Track 2:** Multi-Agent Software Development · [Band of Agents Hackathon](https://lablab.ai/ai-hackathons/band-of-agents-hackathon)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Repo:** [github.com/arun3676/code-tribunal-lab-lab](https://github.com/arun3676/code-tribunal-lab-lab)

---

## Problem

AI coding agents produce large diffs quickly. Standard PR review asks *"is this code correct?"* Tribunal asks *"did the AI build what you actually asked for?"* — reconciling the ticket/spec against the diff before merge.

## How Tribunal works

1. Load a **docket** (ticket + diff + touched files/domains).
2. **CLERK** opens a Band room and routes `@mention` handoffs.
3. **ADVOCATE** extracts requirements; **SURVEYOR** inspects implementation.
4. **GHOST** finds **negative space** (requested but missing work).
5. **DRIFT** finds **scope creep** (unauthorized changes).
6. **WARDEN** is recruited mid-trial when auth/security is touched.
7. **ARBITER** issues verdict, trust score (0–100), merge decision, and traceability ledger.

## Agent roster

| Agent | Role | Provider |
|-------|------|----------|
| CLERK | Orchestrator | Band |
| ADVOCATE | Intent witness | AI/ML API (deterministic fallback) |
| SURVEYOR | Implementation witness | Code Council |
| GHOST | Omission auditor | AI/ML API (deterministic fallback) |
| DRIFT | Scope auditor | Featherless (deterministic fallback) |
| WARDEN | Security witness | Band recruited |
| ARBITER | Judge | AI/ML API (deterministic fallback) |

## Band coordination

Tribunal uses Band as the active coordination layer:

- CLERK creates a Band room.
- Agents are recruited as participants.
- Directed `@mention` messages trigger handoffs.
- Structured Events record requirements, findings, omissions, drift, constraints, and verdicts.
- WARDEN is recruited mid-trial when security-sensitive code is detected.

Set `BAND_ENABLED=true`, `BAND_STRICT=true`, and agent UUIDs for live mirroring. Run `python scripts/verify_band_trial.py` before deploy.

## Demo fixture

**auth-login-001** (hero case):

- Ticket requests secure login: endpoint, bcrypt, rate limiting, audit log, tests, no auth middleware change.
- Diff implements login + bcrypt + audit + tests but **omits rate limiting** (GHOST / R3).
- Diff **changes auth middleware** without authorization (DRIFT).
- WARDEN recruited → **DOES_NOT_CONFORM**, Trust Score ~35/100, **BLOCK**.

**health-check-002** — clean pass case.

## Partner technology

- **Band** — coordination layer (rooms, participants, @mentions, structured events).
- **Featherless AI** — enriches DRIFT scope-drift explanation when `FEATHERLESS_API_KEY` is set.
- **AI/ML API** — planned for intent extraction and adjudication; deterministic fallbacks preserve demo reliability when unavailable.
- Deterministic fallbacks ensure the hero demo always lands.

## Local run

```bash
git clone https://github.com/arun3676/code-tribunal-lab-lab.git
cd code-tribunal-lab-lab
cp .env.example .env    # add LLM + Band keys
python scripts/check_env_keys.py
python scripts/verify_band_trial.py   # Band smoke test
docker compose up --build
```

Open [http://localhost:3000/tribunal](http://localhost:3000/tribunal) · API [http://localhost:8000/health](http://localhost:8000/health)

**Production:** [code-council.vercel.app/tribunal](https://code-council.vercel.app/tribunal)

```bash
curl -N -X POST http://localhost:8000/tribunal/run \
  -H "Content-Type: application/json" \
  -d '{"fixture_id":"auth-login-001"}'
```

## Other modes

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
