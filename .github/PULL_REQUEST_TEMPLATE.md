## What & why

<!-- One or two sentences: what changes, and what problem it solves. -->

## Checklist

- [ ] `python -m pytest -q` passes offline in `apps/api` (no keys needed)
- [ ] `python -m ruff check .` clean in `apps/api`
- [ ] `pnpm lint && pnpm typecheck && pnpm build` clean in `apps/web` (if web touched)
- [ ] Demo fixture verdicts unchanged (`tests/test_fixtures.py`) — they are pinned deterministic
- [ ] `CHANGELOG.md` updated for user-visible changes
