# Target Layout

```text
code-council/
├── apps/
│   ├── web/                 # Next.js 15 frontend (Vercel)
│   └── api/                 # FastAPI backend (Railway)
├── legacy/                  # ARCHIVE bucket from triage
├── docs/
│   ├── TRIAGE.md
│   ├── TARGET_LAYOUT.md
│   └── ARCHITECTURE.md
├── .github/workflows/       # CI for type-check + lint
├── README.md
└── .gitignore
```

## Backend Layout

```text
apps/api/
├── code_council/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── models.py
│   ├── prompts.py
│   ├── utils.py
│   ├── language.py
│   ├── multimodal.py
│   ├── github.py
│   ├── fixes.py
│   ├── server.py
│   └── scanners/
│       ├── __init__.py
│       ├── security.py
│       └── performance.py
├── pyproject.toml
├── Dockerfile
└── .env.example
```

## Frontend Layout

```text
apps/web/
├── package.json
├── next.config.ts
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
├── components.json
├── public/
│   └── favicon.svg
└── src/
    ├── app/
    │   ├── globals.css
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── design/
    │   │   └── page.tsx
    │   └── api/
    ├── components/
    │   ├── effects/
    │   │   └── matrix-rain.tsx
    │   ├── shell/
    │   ├── verdict/
    │   ├── council/
    │   └── ui/
    └── lib/
        ├── api.ts
        ├── sse.ts
        └── utils.ts
```

## Migration Rules

- `apps/api/` becomes the only Python runtime.
- `apps/web/` becomes the only user-facing UI.
- `legacy/` stores archived modules unchanged where practical.
- `docs/` is the canonical architecture and migration reference.
- Root config files should assume a monorepo, not a single Streamlit app.
