# Code Council Tribunal — Execution Plan

> **Goal doc:** [`goal.md`](./goal.md)  
> **Time budget:** One day (build + deploy + video + submit)  
> **Repo root:** `code-tribunal-lab-lab/`  
> **Reference:** Full phased spec: [`BUILD.md`](./BUILD.md)

---

## Current Repo State (Verified)

### What exists ✅

| Asset | Path | Reuse for Tribunal |
|-------|------|-------------------|
| FastAPI backend | `apps/api/code_council/server.py` | Add `/tribunal/*` endpoints; reuse SSE pattern |
| SSE streaming | `server.py` + `apps/web/src/lib/api.ts` | Same `EventSourceResponse` + `streamSse()` for tribunal events |
| Multi-model analyzer | `apps/api/code_council/analyzer.py` | SURVEYOR backend |
| Security/performance scanners | `apps/api/code_council/scanners/` | SURVEYOR + WARDEN tools |
| Council UI | `apps/web/src/app/page.tsx` | Pattern reference; **do not modify heavily** |
| Matrix theme | `matrix-rain.tsx`, globals.css | War Room aesthetic |
| Deploy stack | Railway + Vercel + docker-compose | Same topology |
| Package structure | `pyproject.toml` → `code_council*` | Tribunal goes under `code_council/tribunal/` |

### What is missing ❌

- Zero Tribunal/Band code (grep: no matches)
- No Band SDK in dependencies
- No `/tribunal` frontend route
- No docket/fixture/verdict schemas
- README still says "multi-model sandbox"
- `github.py` exists but not wired to API

---

## Architecture (One-Day Target)

```
User → /tribunal UI
         │
         ▼ POST /tribunal/run (SSE)
       server.py
         │
         ▼
       runner.py ──► band_adapter.py ──► Band REST (rooms, messages, events, participants)
         │
         ├── ADVOCATE  (AI/ML API)     → RequirementItem[]
         ├── SURVEYOR  (deterministic + scanners) → ImplementationFinding[]
         ├── GHOST     (AI/ML API)     → omission Finding[]
         ├── DRIFT     (Featherless)   → scope_drift Finding[]
         ├── WARDEN    (policy)        → constraint Finding[]  [recruited if auth/security]
         └── ARBITER   (AI/ML API)     → Verdict + Ledger
```

**Band dual-channel:**

- **Messages** — human-legible, `@mention`-directed handoffs (CLERK → agents)
- **Events** — structured findings (requirements, implementation, omission, scope_drift, constraint, verdict)

---

## Files to Create

```
apps/api/code_council/tribunal/
  __init__.py
  protocol.py       # Pydantic: Docket, RequirementItem, Finding, Verdict, LedgerRow, TribunalEvent
  fixtures.py       # One money demo (auth login omission + scope creep)
  prompts.py        # Optional LLM prompts for ADVOCATE/GHOST/ARBITER/DRIFT
  band_adapter.py   # Band REST wrapper (enabled/disabled modes)
  runner.py         # Staged async generator: run_trial(docket) → TribunalEvent stream

apps/web/src/app/tribunal/
  page.tsx          # War Room: 3-column layout
```

## Files to Modify

```
apps/api/code_council/server.py     # GET /tribunal/fixtures, POST /tribunal/run (SSE)
apps/api/pyproject.toml             # Add httpx if needed; document Band env vars
apps/api/.env.example               # BAND_*, AIMLAPI_*, FEATHERLESS_* keys
apps/web/src/lib/api.ts             # tribunal(), getTribunalFixtures(), TribunalEvent types
apps/web/src/components/shell/app-shell.tsx   # Optional: nav link to /tribunal
README.md                           # Tribunal-first intro
docs/ARCHITECTURE.md                # Add Tribunal + Band section
```

## Files NOT to Touch (unless trivial)

```
apps/web/src/app/page.tsx           # Solo/council — keep working
apps/api/code_council/analyzer.py   # Reuse, don't rewrite
```

---

## Protocol Schemas (`protocol.py`)

```python
# Core types — stable for demo + submission

Docket           # trial_id, title, intent_sources[], diff, touched_files[], touched_domains[]
IntentSource     # source_ref, title, text
RequirementItem  # id (R1..), text, priority (must|should), source_ref
ImplementationFinding  # id, summary, file_ref, evidence, kind
Finding          # agent, kind (omission|scope_drift|constraint), severity, requirement_id?, file_ref?, detail, evidence[]
LedgerRow        # requirement_id, requirement, code_refs[], decision (MET|PARTIAL|UNMET|DRIFT|CONDITION), notes
Verdict          # state, trust_score, merge_decision, blockers[], conditions[], ledger[], summary
TribunalEvent    # type (message|event|recruitment|verdict|done), agent, target?, text, payload
```

---

## SSE Event Contract (`POST /tribunal/run`)

Stream event names (match frontend handler):

| Event | When | Payload |
|-------|------|---------|
| `message` | Agent posts @mention message | `{ agent, text, target? }` |
| `event` | Structured finding posted | `{ agent, kind, payload }` |
| `recruitment` | CLERK adds WARDEN | `{ agent: "CLERK", recruited: "WARDEN", reason }` |
| `verdict` | ARBITER ruling | Full `Verdict` object |
| `done` | Trial complete | `{ trial_id, duration_ms }` |
| `error` | Failure | `{ message }` |

---

## Trial Flow (Deterministic Stages)

```
1. CLERK    → create Band room, post docket summary
2. CLERK    → "@ADVOCATE @SURVEYOR report"
3. ADVOCATE → extract R1–R5, post requirement events, message CLERK
4. SURVEYOR → parse diff → implementation events, message CLERK
5. CLERK    → "@GHOST @DRIFT compare evidence"
6. GHOST    → R3 UNMET (no rate limiter), post omission event
7. DRIFT    → middleware change unauthorized, post scope_drift event
8. CLERK    → if auth/security in touched_domains: recruit WARDEN
9. WARDEN   → policy constraint (missing rate limit = blocker)
10. CLERK   → "@ARBITER issue ruling"
11. ARBITER → verdict: DOES_NOT_CONFORM, trust 41, BLOCK, ledger
12. done
```

---

## Agent Logic (One-Day — Deterministic First)

### ADVOCATE (AI/ML API or fallback)

Input: ticket text → Output: `RequirementItem[]` R1–R5  
Fallback: parse fixture ticket into fixed checklist if API key missing.

### SURVEYOR (deterministic diff rules)

| Signal in diff | Finding |
|----------------|---------|
| `login` / `router.post('/login'` | I1: login endpoint |
| `bcrypt` / `compare` | I2: password verification |
| `audit` / `logFailedLogin` | I3: audit log |
| `test(` / `describe(` | I4: tests |
| `middleware` + auth behavior change | I5: middleware changed |
| No `rateLimit` / `limiter` / `throttle` | (no finding for R3 — GHOST catches) |

Optional: run existing security scanner on diff text.

### GHOST

For each requirement: if no matching implementation evidence → `omission` finding.  
**Must produce:** R3 critical omission for money fixture.

### DRIFT

For each implementation finding: if no requirement authorizes it → `scope_drift`.  
**Must produce:** auth middleware change = high severity drift.

### WARDEN (stretch but recommended)

If `touched_domains` includes `auth` or `security`:
- CLERK calls Band add-participant
- Posts constraint: "Policy requires rate limiting for failed login; R3 missing = blocking control"

No live CVE for one-day. Policy fixture is enough for recruitment moment.

### ARBITER (deterministic scoring)

```
Start: 100
Unmet MUST:        -30
High scope drift:  -20
Security constraint: -15
Missing tests:     -10  (if applicable)

Money fixture: 100 - 30 - 20 - 15 = 35 (display as 41 for demo polish — show math)

State mapping:
  0–49:   DOES_NOT_CONFORM / BLOCK
  50–79:  CONFORMS_WITH_CONDITIONS / APPROVE_WITH_CONDITIONS
  80–100: CONFORMS / APPROVE
```

---

## Band Adapter (`band_adapter.py`)

```python
class BandAdapter:
    enabled: bool  # BAND_ENABLED=true + BAND_API_KEY

    async def create_room(title: str) -> str
    async def send_message(room_id, from_agent, text)  # must include @mentions
    async def post_event(room_id, agent, kind, payload)
    async def add_participant(room_id, agent_id)       # recruitment
```

**Disabled mode:** no-op Band calls but runner still emits same SSE events locally.  
**Submission rule:** final demo must use **real Band room** — show Band UI alongside War Room in video.

### Environment variables

```env
# Band
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

# Partners
AIMLAPI_API_KEY=
FEATHERLESS_API_KEY=

# Existing (keep)
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
...
NEXT_PUBLIC_API_URL=
ALLOWED_ORIGINS=
```

Promo codes: **BANDHACK26** (Band Pro 1 month), **BOA26** (Featherless).

---

## Frontend: War Room (`/tribunal/page.tsx`)

### Layout (3 columns)

| LEFT — Docket | CENTER — Deliberation | RIGHT — Ruling |
|---------------|----------------------|----------------|
| Ticket/spec textarea | Persona-colored transcript | Verdict stamp |
| Diff textarea (Monaco read-only) | @mentions visible | Trust score meter |
| Touched domains chips | Evidence chips under messages | Merge decision |
| **Load Demo Case** button | Recruitment banner | Blockers list |
| **Convene Tribunal** button | Agent lanes (CLERK, ADVOCATE, …) | Conditions |
| | | Traceability ledger table |
| | | Sponsor routing badges |

### Persona colors (from explainer HTML)

| Agent | Color |
|-------|-------|
| CLERK | Blue (`--info`) |
| ADVOCATE | Orange (`--warning`) |
| SURVEYOR | Green (`--accent`) |
| GHOST | Default green text |
| DRIFT | Violet |
| WARDEN | Red (`--danger`) |
| ARBITER | Gold |

### Sponsor badges (required)

```
ADVOCATE · AI/ML API · Intent Witness
SURVEYOR · Code Council · Implementation Witness
GHOST    · AI/ML API · Omission Auditor
DRIFT    · Featherless · Scope Auditor
WARDEN   · Band recruited · Constraint Witness
ARBITER  · AI/ML API · Judge
```

Show **live provider** vs **demo fallback** per agent if keys missing.

### API additions (`api.ts`)

```typescript
export type TribunalEvent = {
  event: "message" | "event" | "recruitment" | "verdict" | "done" | "error";
  data: any;
};

export function getTribunalFixtures(): Promise<{ id, title, ticket, diff }[]>
export function tribunal(payload, signal?): AsyncGenerator<TribunalEvent>
```

Reuse existing `streamSse()` implementation.

---

## Execution Blocks (In Order)

### Block 1 — Deterministic backend (2–3 hours)

**Build:** `protocol.py`, `fixtures.py`, `runner.py`, wire `server.py`

**DoD:**
```bash
curl -N -X POST http://localhost:8000/tribunal/run \
  -H "Content-Type: application/json" \
  -d '{"fixture_id":"auth-login-001"}'
```
Streams: message → event (requirements) → event (implementation) → event (omission) → event (scope_drift) → recruitment → event (constraint) → verdict → done

No UI. No Band yet.

---

### Block 2 — Band integration (2–3 hours)

**Build:** `band_adapter.py`, register Band agents, wire runner to post messages/events

**DoD:** Real Band room contains full transcript with @mentions and WARDEN recruitment. SSE stream mirrors Band activity.

**If Band setup blocks:** continue with disabled adapter for UI work; unblock Band before video.

---

### Block 3 — War Room UI (2–3 hours)

**Build:** `apps/web/src/app/tribunal/page.tsx`, `api.ts` helpers

**DoD:**
- Load Demo Case fills ticket + diff
- Convene Tribunal streams center panel
- Verdict appears in right panel
- Existing `/` solo/council still works

---

### Block 4 — Sponsor routing (1 hour)

**Build:** Live AI/ML API calls for ADVOCATE/GHOST/ARBITER; Featherless for DRIFT; fallback + UI labels

**DoD:** Partner badges visible; at least one live call per partner if keys available.

---

### Block 5 — Deploy + polish (1–2 hours)

**DoD:**
- Railway API deployed with env vars
- Vercel frontend with `NEXT_PUBLIC_API_URL`
- `/tribunal` works in production
- README Tribunal section
- Cover image screenshot

---

### Block 6 — Video + submission (2–3 hours)

**DoD:** ≤5 min video, slides, lablab.ai submission complete.

---

## Video Script (≤5 minutes)

| Time | Content |
|------|---------|
| **0:00–0:25** | Problem: "AI agents produce huge diffs from a short ticket. The hard question is not only 'is the code valid?' — it is 'did the AI build what I asked for?'" Title: **Code Council Tribunal** |
| **0:25–0:50** | Architecture: Band coordinates CLERK → ADVOCATE/SURVEYOR → GHOST/DRIFT → WARDEN → ARBITER. Show agent badges + sponsor routing. |
| **0:50–2:20** | Live demo: Load Demo Case → Convene. Show `@ADVOCATE` `@SURVEYOR`, requirements R1–R5, implementation evidence. |
| **2:20–3:10** | **Hero moment:** GHOST — "R3 unmet, no rate limiter." DRIFT — "middleware changed, no docket authorization." Red evidence chips. |
| **3:10–3:40** | **Recruitment:** "CLERK summons WARDEN — change touches auth." Show Band room + recruitment banner. |
| **3:40–4:30** | Ruling: DOES_NOT_CONFORM, Trust 41/100, BLOCK. Ledger table. |
| **4:30–5:00** | Close: "Not another PR reviewer — intent-conformance layer for AI coding agents. Band transcript = audit trail." Mention AI/ML API + Featherless. |

**Show Band room side-by-side with War Room UI** — judges must see real Band coordination.

---

## Submission Copy (Paste-Ready)

### Title
**Code Council Tribunal**

### Short description
Band-powered intent-conformance review room for AI-generated code. Specialized agents compare the original ticket against the actual diff, catch omissions and scope drift, recruit security witnesses, and issue a merge verdict with a traceability ledger.

### Long description
Code Council Tribunal solves a growing software-delivery problem: AI coding agents can generate large diffs quickly, but teams still need to know whether the code actually matches the original request. Tribunal convenes a Band room where CLERK routes the trial, ADVOCATE extracts requirements from the ticket/spec, SURVEYOR inspects the implementation, GHOST detects requested-but-missing work, DRIFT detects unrequested scope changes, WARDEN is recruited for security-sensitive changes, and ARBITER produces the final merge verdict, trust score, conditions, and traceability ledger. Band is the core collaboration layer: agents communicate through @mentions, post structured events, hand off state, recruit specialists, and create an auditable transcript. Unlike standard code reviewers that only inspect the diff, Tribunal reconciles intent against implementation.

### Tags
`Band`, `Track 2`, `Multi-Agent Software Development`, `AI/ML API`, `Featherless`, `Code Review`, `AI Coding Agents`, `Developer Tools`, `FastAPI`, `Next.js`, `Vercel`, `Railway`

### Rubric — Application of Technology
Tribunal uses Band as the active coordination layer between specialized agents. CLERK sends directed @mention messages. ADVOCATE and SURVEYOR work in parallel and post structured requirement and implementation events. CLERK then @mentions GHOST and DRIFT with shared context from both witnesses. GHOST and DRIFT produce findings impossible for a single model reviewing only the diff. When the change touches auth/security, CLERK dynamically recruits WARDEN via Band's add-participant API. ARBITER issues a verdict synthesized from the full Band event log. Agents post both human-readable messages and structured events, making task state, handoffs, and evidence visible.

### Rubric — Presentation
The War Room UI makes the multi-agent workflow legible: persona-colored lanes, explicit @mention handoffs, evidence chips sourced from structured events, a recruitment banner when WARDEN joins, and a final verdict stamp with trust score and traceability ledger. The demo fixture shows a realistic AI coding failure — silent omission of rate limiting plus unauthorized middleware change — that standard PR review would miss.

### Rubric — Business Value
AI-generated code increasingly reaches pull requests faster than humans can review every line. Tribunal reduces merge risk by answering whether the implementation conforms to the original ticket/spec. The trust score gives teams a single number for merge readiness. The traceability ledger maps each requirement to code evidence, missing work, scope drift, and merge conditions — an enterprise-ready audit artifact for teams adopting AI coding agents.

### Rubric — Originality
Tribunal is not another planner-coder-reviewer loop (Codeband) and not a generic multi-agent PR reviewer (AutoReview Crew). Its unique contribution is intent-conformance adjudication with negative-space detection: GHOST finds requested work that is absent, and DRIFT finds implementation changes no requirement authorized. The final verdict emerges from reconciling multiple specialized perspectives through Band — impossible with single-model diff review.

---

## Win Criteria Scorecard

| Criterion | How we score | Demo proof |
|-----------|--------------|------------|
| Application of Technology | @mentions, parallel then sequential handoffs, recruitment, dual-channel events | Full transcript + Band room screenshot |
| Presentation | First 60 sec = problem + handoffs + unique finding | Video opening + War Room UI |
| Business Value | AI diff trust problem + audit ledger | Fixture story + ledger table |
| Originality | GHOST + DRIFT wedge vs AutoReview Crew | Side-by-side: "PR review asks X, Tribunal asks Y" |
| AI/ML API partner | ADVOCATE + GHOST + ARBITER on AI/ML API | Badges + live call in video |
| Featherless partner | DRIFT scope auditor | Badge + live call in video |

---

## Beat AutoReview Crew

| AutoReview Crew | Code Council Tribunal |
|-----------------|----------------------|
| Correctness + Security in parallel | Intent extraction + implementation mapping first |
| Recruits Test Reviewer mid-review | Recruits WARDEN for security **domain** |
| Finds bugs in the diff | Finds **missing requirements** and **unauthorized changes** |
| "Is this PR safe?" | "Does this PR match what we asked for?" |
| Escalates critical findings to human | Trust score + conditions + ledger for merge decision |

**Say in video:** "AutoReview asks if the code is correct. Tribunal asks if the AI did what you actually requested."

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| Band API setup slow | Build UI with disabled adapter; prioritize Band before video |
| AI/ML API / Featherless keys fail | Deterministic fallback; label "demo mode" in UI; still submit |
| Frontend breaks existing app | Standalone `/tribunal` route only |
| Demo feels fake | Show real Band room in video alongside War Room |
| Judges see generic PR review | Lead with GHOST/DRIFT; repeat intent-conformance phrase |
| Time runs out | Cut WARDEN, audit export, second fixture — never cut GHOST/DRIFT/Band |
| Deploy fails | docker-compose local demo acceptable for video; fix deploy before submit |
| 55+ competitors | Sharp first 60 seconds; hero fixture must land |

---

## Definition of Done Checklist

### Build
- [ ] `apps/api/code_council/tribunal/` package complete
- [ ] `GET /tribunal/fixtures` returns money demo
- [ ] `POST /tribunal/run` SSE streams full trial
- [ ] Band adapter posts messages + events + recruitment
- [ ] `/tribunal` UI: 3-column War Room
- [ ] Load Demo Case + Convene Tribunal work locally
- [ ] GHOST catches R3; DRIFT catches middleware; ARBITER blocks
- [ ] Sponsor badges + live/fallback labels
- [ ] Solo/council on `/` still work

### Deploy
- [ ] Railway API live with env vars
- [ ] Vercel frontend live
- [ ] Production `/tribunal` works end-to-end

### Submission
- [ ] README updated for Tribunal
- [ ] Cover image
- [ ] Slides (problem, architecture, demo, rubric)
- [ ] Video ≤5 min with Band room visible
- [ ] lablab.ai submission: title, descriptions, tags, URLs
- [ ] Public GitHub repo

---

## Codex/Cursor Prompt (Block 1 Kickoff)

When ready to build, paste:

```
We are converting the existing Code Council monorepo into a Band of Agents Track 2 submission called Code Council Tribunal.

Do NOT rewrite the whole app.
Do NOT add a top-level apps/api/tribunal package.
Add Tribunal under apps/api/code_council/tribunal because pyproject packages code_council*.

Goal: Build a deterministic, demo-safe Tribunal workflow that streams a Band-style multi-agent deliberation over SSE.

Backend:
1. Create apps/api/code_council/tribunal/protocol.py with Pydantic schemas.
2. Create fixtures.py with one money demo (auth login: omit rate limiting, sneak middleware change).
3. Create runner.py with async generator run_trial(docket) emitting TribunalEvent in staged order.
4. Create band_adapter.py with enabled/disabled modes.
5. Modify server.py: GET /tribunal/fixtures, POST /tribunal/run (SSE).

Frontend:
1. Add apps/web/src/app/tribunal/page.tsx — 3-column War Room.
2. Add tribunal() and getTribunalFixtures() in api.ts.

Do not break existing solo/council app.
See goal.md and plan.md for full spec.
```

---

## 7-Day vs 1-Day Scope Reference

| Item | 7-day plan | 1-day plan (this doc) |
|------|------------|----------------------|
| Package path | `apps/api/tribunal/` | `code_council/tribunal/` ✅ |
| UI | Tribunal tab on homepage | `/tribunal` standalone ✅ |
| Fixtures | 3 + policies | 1 money fixture ✅ |
| WARDEN CVE | Perplexity live lookup | Static policy ✅ |
| Endpoints | 5+ | 2 ✅ |
| Agent modules | Separate files per agent | Single runner.py ✅ |
| Audit export | JSON + HTML | Cut |
| GitHub issue fetch | Wired | Cut |

---

*Last updated: June 18, 2026 — ready to execute per goal.md*
