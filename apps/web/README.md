# Code Tribunal Web

Next.js 15 frontend for [Code Tribunal](https://github.com/arun3676/code-tribunal) — the landing
demo for the engine that ships as a CLI + MCP server.

## Routes

| Path | Description |
|------|-------------|
| `/` | Animated marketing landing (motion-driven hero, scripted verdict demo) |
| `/tribunal` | **War Room** — Band deliberation, verdict stamp, trust meter, ledger |
| `/council` | Solo + Council analysis (Monaco editor, SSE streaming) |
| `/about` | Project overview |

Header nav includes **Council** and **Tribunal** links (`app-shell.tsx`); the landing has its own header/footer.

## Tribunal UI

- **Left:** Docket — ticket, diff (Monaco), domain chips, fixture picker
- **Center:** Deliberation stream — persona avatars, @mentions, evidence chips, WARDEN recruitment
- **Right:** Ruling — verdict stamp, trust meter, blockers, conditions, traceability ledger, band mode badge

Components live in `src/components/tribunal/`.

## Local run

```bash
cd apps/web
cp .env.example .env.local
pnpm install
pnpm dev
```

Set `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

Or from repo root: `docker compose up`

## Deploy

Vercel — see root [`DEPLOYMENT.md`](../../DEPLOYMENT.md).
