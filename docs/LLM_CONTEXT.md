# Code Council Tribunal — LLM Context Reference

> **Purpose of this file:** Upload this single document to ChatGPT, Claude, Gemini, or any LLM to get full product context without reading the repo. The model should use this to suggest next steps, research gaps, review architecture, or help implement the hackathon build.
>
> **Last updated:** June 18, 2026  
> **Repo:** https://github.com/arun3676/code-tribunal-lab-lab  
> **Hackathon:** Band of Agents · Track 2 · Deadline June 19, 2026 8:00 AM PDT  
> **Build status:** Code Council base is live; **Tribunal (Band multi-agent layer) is NOT built yet**

---

## Instructions for the LLM reading this file

You are advising on **Code Council Tribunal** — a hackathon submission for the Band of Agents event (lablab.ai). When responding:

1. **Assume Tribunal is the priority** — the existing Solo/Council UI is a foundation, not the submission story.
2. **Respect constraints** — one-day build budget, no scope creep (see Non-Goals).
3. **Optimize for judges** — visible Band handoffs in first 60 seconds; GHOST + DRIFT hero moment.
4. **Research usefully** — Band Agent API, AI/ML API, Featherless, competitor submissions, intent-conformance / spec-grounded code review literature.
5. **Suggest concrete next steps** — file paths, endpoints, acceptance criteria, not vague advice.

---

## 1. Executive summary

**Product name:** Code Council Tribunal  
**One-line pitch:** Did the AI build what you actually asked for?  
**Category:** Not code review — **intent-conformance review** for AI-generated diffs.

**Problem:** AI coding agents (Cursor, Copilot, Codex, Devin) produce large diffs quickly. Standard PR bots ask *"is this code correct?"* They cannot ask *"is this what was requested?"* because intent lives in the ticket/spec, outside the repo.

**Solution:** A Band-powered agent court that:
- Extracts requirements from the ticket (ADVOCATE)
- Inspects what the diff actually changed (SURVEYOR)
- Finds **missing** requested work (GHOST — negative space)
- Finds **unauthorized** changes (DRIFT — scope creep)
- Recruits security witness when needed (WARDEN)
- Issues merge verdict + trust score + traceability ledger (ARBITER)

**Coordination layer:** [Band](https://band.ai) — real @mention routing, structured events, mid-trial recruitment. Band must NOT be a thin wrapper.

---

## 2. Current state vs planned

### ✅ Built today (Code Council base)

| Component | Path | Status |
|-----------|------|--------|
| FastAPI backend | `apps/api/code_council/server.py` | Live |
| Multi-model analyzer | `apps/api/code_council/analyzer.py` | Gemini, DeepSeek, Mercury, Kimi |
| Security scanner | `apps/api/code_council/scanners/security.py` | Live |
| Performance scanner | `apps/api/code_council/scanners/performance.py` | Live |
| SSE streaming | `server.py` + `apps/web/src/lib/api.ts` | Live |
| Solo + Council UI | `apps/web/src/app/page.tsx` (~765 lines) | Live |
| Multimodal | `multimodal.py` + UI panel | Live |
| GitHub helpers | `github.py` | Exists, **not wired to API** |
| Deploy | Railway (api) + Vercel (web) | Configured |
| CI | `.github/workflows/ci.yml` | api import + web build |

### ❌ Not built yet (Tribunal — the hackathon deliverable)

| Component | Planned path | Status |
|-----------|--------------|--------|
| Tribunal package | `apps/api/code_council/tribunal/` | **Missing** |
| Band adapter | `tribunal/band_adapter.py` | **Missing** |
| Trial runner | `tribunal/runner.py` | **Missing** |
| Protocol schemas | `tribunal/protocol.py` | **Missing** |
| Demo fixture | `tribunal/fixtures.py` | **Missing** |
| API endpoints | `GET /tribunal/fixtures`, `POST /tribunal/run` | **Missing** |
| War Room UI | `apps/web/src/app/tribunal/page.tsx` | **Missing** |
| Band SDK | `pyproject.toml` | **Not added** |

**Critical:** Zero matches for `tribunal` or `band` in codebase today.

---

## 3. Repository structure

```
code-tribunal-lab-lab/                 # monorepo root (= workspace root)
├── apps/
│   ├── api/
│   │   ├── code_council/            # ONLY Python package (pyproject: code_council*)
│   │   │   ├── server.py            # FastAPI app — add /tribunal/* here
│   │   │   ├── analyzer.py
│   │   │   ├── scanners/
│   │   │   ├── github.py            # reserved for docket ingestion
│   │   │   └── tribunal/            # CREATE THIS — do NOT use apps/api/tribunal/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── railway.json
│   └── web/
│       ├── src/app/
│       │   ├── page.tsx             # Solo/Council — do NOT break
│       │   ├── about/page.tsx
│       │   └── tribunal/page.tsx    # CREATE THIS
│       ├── src/lib/api.ts           # add tribunal() SSE client
│       └── src/components/
├── docs/
│   ├── LLM_CONTEXT.md               # this file
│   ├── ARCHITECTURE.md
│   ├── STRUCTURE.md
│   ├── tribunal-explainer.html        # judge pitch deck
│   └── hackathon/
│       ├── goal.md
│       ├── plan.md
│       └── BUILD.md                   # full 7-day phased spec
├── docker-compose.yml
├── .env.example
├── README.md
└── DEPLOYMENT.md
```

**Packaging rule:** Tribunal MUST live under `code_council/tribunal/` because `pyproject.toml` only packages `code_council*`. A sibling `apps/api/tribunal/` package will break deploy.

**UI rule:** Add standalone `/tribunal` route. Do NOT heavily edit `page.tsx` (complex solo/council/multimodal state).

---

## 4. Existing API (today)

| Method | Path | Type | Purpose |
|--------|------|------|---------|
| GET | `/health` | JSON | Health check |
| GET | `/models` | JSON | Available LLM providers |
| POST | `/scan` | JSON | Static security + performance scan |
| POST | `/analyze` | SSE | Single-model streaming analysis |
| POST | `/council` | SSE | Parallel multi-model council |
| POST | `/multimodal` | JSON | Image analysis |

**SSE pattern (reuse for Tribunal):** `sse-starlette` `EventSourceResponse` + async queue. Frontend uses manual SSE frame parsing in `streamSse()` inside `api.ts`.

**Planned Tribunal endpoints:**

| Method | Path | Type | Purpose |
|--------|------|------|---------|
| GET | `/tribunal/fixtures` | JSON | Return demo cases |
| POST | `/tribunal/run` | SSE | Stream full trial |

---

## 5. Tribunal architecture (target)

```
User → /tribunal UI
         │
         ▼ POST /tribunal/run (SSE)
       server.py
         │
         ▼
       runner.py ──► band_adapter.py ──► Band REST
         │              (rooms, @mention messages, events, add participant)
         │
         ├── CLERK      orchestrator (Band)
         ├── ADVOCATE   requirements from ticket (AI/ML API)
         ├── SURVEYOR   diff analysis (Code Council + deterministic rules)
         ├── GHOST      omissions (AI/ML API)
         ├── DRIFT      scope creep (Featherless)
         ├── WARDEN     security/policy (recruited live if auth/security)
         └── ARBITER    verdict + trust score + ledger (AI/ML API)
```

### Band dual-channel (judge-critical)

| Channel | Purpose | @mentions required? |
|---------|---------|---------------------|
| **Messages** | Human-legible handoffs in transcript | Yes — only mentioned agents process |
| **Events** | Structured findings (requirements, omissions, verdict) | No — audit/machine layer |

**Recruitment:** `POST /agent/chats/{id}/participants` — CLERK adds WARDEN mid-trial; must be visible in UI + video.

---

## 6. Agent cast

| Agent | Role | Provider | When |
|-------|------|----------|------|
| **CLERK** | Orchestrator — opens room, @mentions, recruits | Band | Always |
| **ADVOCATE** | Intent witness → R1, R2… requirement checklist | AI/ML API | Always |
| **SURVEYOR** | Implementation witness → what diff changed | Code Council analyzer | Always |
| **GHOST** | Omission auditor — asked but **missing** | AI/ML API | After ADVOCATE + SURVEYOR |
| **DRIFT** | Scope auditor — done but **not authorized** | Featherless | After ADVOCATE + SURVEYOR |
| **WARDEN** | Constraint witness — security/policy | Band + policy | Recruited if auth/security touched |
| **ARBITER** | Judge — verdict, trust score, ledger | AI/ML API | Always |

Minimum hackathon: 3 agents through Band. **Competitive demo: 6–7** with recruitment.

---

## 7. Core thesis — intent ceiling

Frontier reviewers (Greptile, Devin, Codex, CodeRabbit) sit **inside the diff**. They answer *"is this code correct?"*

Tribunal crosses the **intent ceiling** by reconciling **external intent** (ticket/spec) against **implementation** (diff).

**Three lenses competitors structurally miss:**
1. **Omission (GHOST)** — what was asked but is absent (negative space)
2. **Scope drift (DRIFT)** — what was done but nobody asked for
3. **Intent-anchored constraint (WARDEN)** — does it break a rule given what it's trying to do

**Output artifacts:**
- **Verdict:** `CONFORMS` | `CONFORMS_WITH_CONDITIONS` | `DOES_NOT_CONFORM`
- **Trust Score:** 0–100
- **Traceability Ledger:** intent item ↔ code ↔ decision
- **Deliberation Transcript:** Band room (primary demo artifact)

---

## 8. Hero demo fixture (must work reliably)

**Fixture ID:** `auth-login-001`

**Ticket — Implement secure login:**
- R1: Add `/api/login` endpoint — MUST
- R2: Verify password using bcrypt — MUST
- R3: Rate-limit failed logins (5 per 15 min) — MUST
- R4: Add audit log for failed login — MUST
- R5: Add regression tests — MUST
- **Constraint:** Do not change existing auth middleware behavior

**Diff intentionally:**
- ✅ R1, R2, R4, one test
- ❌ Omits R3 (rate limiting)
- ⚠️ Sneaks auth middleware behavior change

**Expected trial outcome:**
- GHOST → R3 unmet (critical omission)
- DRIFT → unauthorized middleware change
- CLERK recruits WARDEN (auth domain)
- ARBITER → `DOES_NOT_CONFORM`, trust ~41/100, `BLOCK`

This is the **60-second judge moment** — normal diff review misses both failures.

---

## 9. Protocol schemas (to implement)

```python
# apps/api/code_council/tribunal/protocol.py

Docket           # trial_id, title, intent_sources[], diff, touched_files[], touched_domains[]
RequirementItem  # id (R1..), text, priority (must|should), source_ref
ImplementationFinding  # id, summary, file_ref, evidence, kind
Finding          # agent, kind (omission|scope_drift|constraint), severity, detail, evidence[]
LedgerRow        # requirement_id, code_refs[], decision (MET|UNMET|DRIFT|CONDITION), notes
Verdict          # state, trust_score, merge_decision, blockers[], conditions[], ledger[], summary
TribunalEvent    # type (message|event|recruitment|verdict|done), agent, text, payload
```

### SSE events from POST /tribunal/run

| Event | When |
|-------|------|
| `message` | Agent @mention message |
| `event` | Structured finding |
| `recruitment` | WARDEN added to room |
| `verdict` | ARBITER ruling |
| `done` | Trial complete |
| `error` | Failure |

### Trial flow (12 steps)

```
CLERK opens room → @ADVOCATE @SURVEYOR
ADVOCATE posts R1–R5 → SURVEYOR posts implementation findings
CLERK → @GHOST @DRIFT
GHOST: R3 unmet → DRIFT: middleware unauthorized
CLERK recruits WARDEN → WARDEN: policy constraint
CLERK → @ARBITER → verdict → done
```

### Trust score (deterministic)

```
Start: 100
Unmet MUST: -30 | High scope drift: -20 | Security constraint: -15 | Missing tests: -10
0–49: DOES_NOT_CONFORM / BLOCK
50–79: CONFORMS_WITH_CONDITIONS
80–100: CONFORMS / APPROVE
```

---

## 10. Files to create (implementation checklist)

### Create
```
apps/api/code_council/tribunal/__init__.py
apps/api/code_council/tribunal/protocol.py
apps/api/code_council/tribunal/fixtures.py
apps/api/code_council/tribunal/prompts.py
apps/api/code_council/tribunal/band_adapter.py
apps/api/code_council/tribunal/runner.py
apps/web/src/app/tribunal/page.tsx
```

### Modify
```
apps/api/code_council/server.py          # /tribunal/fixtures, /tribunal/run
apps/api/.env.example                    # BAND_*, AIMLAPI_*, FEATHERLESS_*
apps/web/src/lib/api.ts                  # tribunal(), getTribunalFixtures()
apps/web/src/components/shell/app-shell.tsx  # optional nav link
```

### Do NOT touch (unless trivial)
```
apps/web/src/app/page.tsx                # solo/council — keep working
apps/api/code_council/analyzer.py        # reuse, don't rewrite
```

---

## 11. War Room UI spec

**Route:** `/tribunal` — standalone page, 3 columns:

| LEFT — Docket | CENTER — Deliberation | RIGHT — Ruling |
|---------------|----------------------|----------------|
| Ticket textarea | Persona-colored transcript | Verdict stamp |
| Diff (Monaco) | @mentions + evidence chips | Trust score meter |
| Touched domains | Recruitment banner | Merge decision + ledger |
| Load Demo Case | Agent lanes | Sponsor badges |
| Convene Tribunal | | |

**Persona colors:** CLERK=blue, ADVOCATE=orange, SURVEYOR=green, GHOST=default, DRIFT=violet, WARDEN=red, ARBITER=gold

**Sponsor badges (required for partner prizes):**
- ADVOCATE · AI/ML API
- GHOST · AI/ML API
- ARBITER · AI/ML API
- DRIFT · Featherless
- Show "live" vs "demo fallback" if keys missing

---

## 12. Environment variables

### Existing (Code Council)
```env
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
MERCURY_API_KEY=
Kimi_API_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000
```

### Tribunal / Band (add)
```env
BAND_ENABLED=true
BAND_API_KEY=
BAND_BASE_URL=https://app.band.ai/api/v1
BAND_CLERK_ID=
BAND_ADVOCATE_ID=
BAND_SURVEYOR_ID=
BAND_GHOST_ID=
BAND_DRIFT_ID=
BAND_WARDEN_ID=
BAND_ARBITER_ID=
AIMLAPI_API_KEY=
FEATHERLESS_API_KEY=
```

**Promo codes:** `BANDHACK26` (Band Pro 1 month), `BOA26` (Featherless)

---

## 13. Hackathon requirements

| Requirement | How we satisfy |
|-------------|----------------|
| ≥3 agents through Band during workflow | 6–7 agents with @mentions |
| Band = real collaboration layer | Messages + events + recruitment |
| Track 2: multi-agent software development | Review + merge-prep workflow |
| Public GitHub + demo URL + video ≤5 min | Vercel + Railway |
| MIT-compliant original work | New Band tribunal layer |
| Partner: AI/ML API | ADVOCATE, GHOST, ARBITER |
| Partner: Featherless | DRIFT |

### Judging criteria (Application of Technology = highest weight)

Judges want: visible handoffs, role specialization, shared context, task state — **in first 60 seconds of demo**.

### Submission copy

- **Title:** Code Council Tribunal
- **Short:** Band-powered intent-conformance review room for AI-generated code. Agents compare ticket vs diff, catch omissions and scope drift, issue merge verdict + ledger.
- **Tags:** Band, Track 2, AI/ML API, Featherless, Code Review, AI Coding Agents, FastAPI, Next.js, Vercel, Railway

---

## 14. Competitor differentiation

| Competitor | Their angle | Our counter |
|------------|-------------|-------------|
| **AutoReview Crew** (closest) | 4 agents review PR for bugs/security/tests | We verify PR **matches the request** — GHOST + DRIFT |
| **Codeband** (reference impl) | Planner + coder + reviewer | We **adjudicate**, not author code |
| **DevBand** | Full delivery pipeline | Intent reconciliation before merge |
| **MUSTER** | Incident war-room + recruitment | Same recruitment pattern for merge-prep |
| Generic PR bots | "Is code correct?" | "Did AI build what was asked?" |

**Video line:** "AutoReview asks if the code is correct. Tribunal asks if the AI did what you actually requested."

---

## 15. Execution blocks (build order)

| Block | Work | Definition of done |
|-------|------|-------------------|
| **1** | `protocol.py`, `fixtures.py`, `runner.py`, SSE endpoints | `curl POST /tribunal/run` streams full trial without Band/UI |
| **2** | `band_adapter.py`, real Band room | Transcript with @mentions + WARDEN recruitment in Band |
| **3** | `/tribunal/page.tsx`, `api.ts` | Load Demo Case + Convene Tribunal works |
| **4** | AI/ML API + Featherless routing | Partner badges + live calls or honest fallbacks |
| **5** | Deploy Railway + Vercel | Production `/tribunal` works |
| **6** | Video + lablab.ai submit | ≤5 min video, slides, cover image |

**Priority:** GHOST + DRIFT hero moment first. Cut WARDEN/CVE/export before cutting GHOST/DRIFT/Band.

---

## 16. Non-goals (do NOT suggest these)

- Autonomous coding agent / auto-merge
- Full GitHub PR/Jira/Linear integration
- Persistent database / multi-tenant auth
- Real CVE lookup (WARDEN uses static policy for 1-day build)
- Three fixtures + audit export
- Competing with Codeband on code generation
- Rebuilding homepage — use `/tribunal` route only
- `apps/api/tribunal/` as separate package

---

## 17. Definition of done (submission)

- [ ] `/tribunal` loads on deployed app
- [ ] Money fixture: GHOST catches R3, DRIFT catches middleware
- [ ] Real Band room with @mentions (not fake transcript only)
- [ ] ≥5 agents visible; WARDEN recruitment shown
- [ ] Verdict: DOES_NOT_CONFORM, trust score, BLOCK, ledger
- [ ] Sponsor badges visible
- [ ] Video ≤5 min showing Band room + War Room side by side
- [ ] Submitted on lablab.ai before June 19 8:00 AM PDT

---

## 18. Key decisions (don't re-litigate)

| Decision | Rationale |
|----------|-----------|
| Track 2 | Software delivery / merge-prep |
| Intent-conformance wedge | AutoReview Crew owns generic PR review |
| `code_council/tribunal/` path | pyproject packages `code_council*` only |
| Standalone `/tribunal` route | Don't break solo/council homepage |
| Deterministic runner + optional LLMs | Demo reliability for one-day build |
| Real Band required for submission | Hackathon rejects thin wrappers |
| GHOST + DRIFT first | Hero moment everything else supports |

---

## 19. Tech stack reference

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind, Monaco, manual SSE |
| Backend | FastAPI, Uvicorn, Pydantic, sse-starlette |
| LLMs (today) | Gemini, DeepSeek, Mercury, Kimi via analyzer.py |
| LLMs (Tribunal) | AI/ML API (ADVOCATE/GHOST/ARBITER), Featherless (DRIFT) |
| Coordination | Band Agent API (rooms, messages, events, participants) |
| Deploy | Vercel (web) + Railway (api) + docker-compose (local) |
| State | Stateless — no DB; optional localStorage in frontend |

---

## 20. Local development

```bash
git clone https://github.com/arun3676/code-tribunal-lab-lab.git
cd code-tribunal-lab-lab
cp .env.example .env   # add LLM keys
docker compose up
# Frontend: http://localhost:3000
# API: http://localhost:8000/health
```

Backend only:
```bash
cd apps/api && pip install -e . && uvicorn code_council.server:app --reload
```

Frontend only:
```bash
cd apps/web && pnpm install && pnpm dev
```

---

## 21. Related docs in repo (if you have file access)

| File | Contents |
|------|----------|
| `docs/hackathon/plan.md` | Detailed execution plan, video script, rubric writeups |
| `docs/hackathon/goal.md` | Goals, success criteria, constraints |
| `docs/hackathon/BUILD.md` | Full 7-day phased build spec |
| `docs/tribunal-explainer.html` | Visual pitch deck for judges |
| `docs/ARCHITECTURE.md` | System design |
| `DEPLOYMENT.md` | Railway + Vercel checklist |

---

## 22. What to ask the LLM to do next

Example prompts after uploading this file:

- *"Given this context, what should I build first in the next 2 hours? Give file-by-file steps."*
- *"Review my Band integration approach — will judges see this as real collaboration?"*
- *"Research Band Agent API @mention and recruitment patterns and map them to our trial flow."*
- *"Compare our GHOST/DRIFT wedge vs AutoReview Crew and suggest demo script improvements."*
- *"Write the Block 1 implementation for protocol.py, fixtures.py, runner.py with acceptance tests."*
- *"What are the top 3 risks to winning and how do I mitigate each before submission?"*
- *"Draft lablab.ai submission fields and a 5-minute video script from this spec."*

---

*End of LLM context reference. Single source of truth for product structure as of June 18, 2026.*
