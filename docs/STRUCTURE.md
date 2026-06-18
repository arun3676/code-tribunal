# Repository structure

Layout for **Code Council Tribunal** — Band-powered intent-conformance review for AI-generated code.

```
code-tribunal-lab-lab/
├── apps/
│   ├── api/
│   │   ├── code_council/       # Python runtime
│   │   │   ├── server.py
│   │   │   ├── analyzer.py
│   │   │   ├── scanners/
│   │   │   ├── github.py       # Tribunal docket helpers
│   │   │   └── tribunal/       # (next) Band multi-agent workflow
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── web/
│       ├── src/app/            # /, /about, /tribunal (planned)
│       ├── src/components/
│       └── src/lib/api.ts
├── docs/
│   ├── LLM_CONTEXT.md          # Upload to any LLM for full product context
│   ├── ARCHITECTURE.md
│   ├── STRUCTURE.md
│   ├── tribunal-explainer.html # Judge-facing case file / pitch
│   └── hackathon/
│       ├── goal.md
│       ├── plan.md
│       └── BUILD.md            # Full phased build spec
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── LICENSE
├── README.md
└── DEPLOYMENT.md
```

## Rules

| Path | Purpose |
|------|---------|
| `apps/api/code_council/` | All backend code |
| `apps/web/src/` | All frontend code |
| `docs/hackathon/` | Tribunal goals, execution plan, build phases |
| Root | Monorepo config only — no nested product folders |

## Build target

See [`docs/hackathon/plan.md`](./hackathon/plan.md) for the one-day execution path and [`docs/hackathon/BUILD.md`](./hackathon/BUILD.md) for the full phased spec.
