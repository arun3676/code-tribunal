# Code Council Tribunal

**Did the AI build what you actually asked for?**

Band-powered intent-conformance review for AI-generated code. Code Council streams multi-model analysis today; **Tribunal** (in build) convenes Band-connected agents to verify a diff matches the original ticket — catching omissions, scope drift, and merge risk before ship.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Repo:** [github.com/arun3676/code-tribunal-lab-lab](https://github.com/arun3676/code-tribunal-lab-lab)

## What's live today

| Feature | Description |
|---------|-------------|
| **Solo analysis** | Stream one model's verdict on pasted code |
| **Council** | Run 2–4 models in parallel with consensus matrix |
| **Static scan** | Security + performance rules without LLM |
| **Multimodal** | Image upload for vision models |

## What's next (Tribunal)

Multi-agent Band room: CLERK, ADVOCATE, SURVEYOR, GHOST, DRIFT, WARDEN, ARBITER → merge verdict + trust score + ledger.

→ [`docs/hackathon/plan.md`](docs/hackathon/plan.md) · [`docs/hackathon/goal.md`](docs/hackathon/goal.md) · [`docs/LLM_CONTEXT.md`](docs/LLM_CONTEXT.md) *(upload to ChatGPT/Claude for full context)*

## Stack

Next.js 15 · FastAPI · SSE streaming · Railway + Vercel · Gemini · DeepSeek · Mercury · Kimi

## Quick start

```bash
git clone https://github.com/arun3676/code-tribunal-lab-lab.git
cd code-tribunal-lab-lab
cp .env.example .env    # add LLM keys
docker compose up
```

Open [http://localhost:3000](http://localhost:3000) · API [http://localhost:8000/health](http://localhost:8000/health)

## Layout

```
apps/api/     FastAPI — code_council package (+ tribunal/ next)
apps/web/     Next.js — Council UI (+ /tribunal next)
docs/         Architecture + hackathon plans
```

Full tree: [`docs/STRUCTURE.md`](docs/STRUCTURE.md)

## Deploy

- `apps/api` → Railway
- `apps/web` → Vercel (`NEXT_PUBLIC_API_URL`)

Details: [`DEPLOYMENT.md`](DEPLOYMENT.md)

## License

MIT — see [LICENSE](LICENSE).
