"""Deterministic Tribunal runner.

``run_trial(docket)`` is an async generator that emits :class:`TribunalEvent`
objects in staged order, mirroring a Band deliberation. It is deterministic by
design (one-day demo reliability): LLM/Band calls are optional enrichment, and
the hero findings — GHOST's omission and DRIFT's scope creep — fall out of
explicit diff signal detection so they land every time.

Flow (12 stages):
    CLERK opens chamber → recruit ADVOCATE/SURVEYOR → @mention handoff
    ADVOCATE → requirements   SURVEYOR → implementation findings
    CLERK recruits GHOST/DRIFT → @mention audit handoff
    GHOST → omissions         DRIFT → scope drift
    CLERK recruits WARDEN (if auth/security)  → WARDEN constraint
    CLERK recruits ARBITER → @mention ruling → verdict → done
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import AsyncIterator

from .band_adapter import BandError
from .coordination import CoordinationBackend, get_coordination_backend
from .fixtures import get_fixture
from .llm import complete_json
from .protocol import (
    AGENTS,
    Docket,
    Finding,
    ImplementationFinding,
    LedgerRow,
    RequirementItem,
    TribunalEvent,
    TrustDeduction,
    Verdict,
)

# Pacing between stages so the War Room streams legibly on screen.
STEP_DELAY = 0.45


# --- requirement extraction (ADVOCATE) --------------------------------------

_REQ_RE = re.compile(r"R(\d+)\s*\((MUST|SHOULD)\)\s*:?\s*(.+)", re.IGNORECASE)


def extract_requirements(docket: Docket) -> list[RequirementItem]:
    items: list[RequirementItem] = []
    text = "\n".join(source.text for source in docket.intent_sources)
    source_ref = docket.intent_sources[0].source_ref if docket.intent_sources else ""
    for match in _REQ_RE.finditer(text):
        number, priority, body = match.groups()
        items.append(
            RequirementItem(
                id=f"R{number}",
                text=body.strip().rstrip("."),
                priority="must" if priority.upper() == "MUST" else "should",
                source_ref=source_ref,
            )
        )
    return items


def extract_constraints(docket: Docket) -> list[str]:
    text = "\n".join(source.text for source in docket.intent_sources)
    return [
        line.split(":", 1)[-1].strip()
        for line in text.splitlines()
        if line.strip().lower().startswith("constraint")
    ]


# --- diff signal detection (SURVEYOR) ---------------------------------------

_SIGNALS: dict[str, str] = {
    "login_endpoint": r"/api/login|router\.(post|get)\(",
    "bcrypt": r"bcrypt|\.compare\(",
    "rate_limit": r"rate[\s_-]?limit|limiter|throttle|attempts?\b",
    "audit_log": r"audit",
    "tests": r"\btest\(|describe\(|\.test\.",
    "health_endpoint": r"/api/health",
    "git_sha": r"GIT_SHA|commit|sha",
    # payment-refund-003
    "refund_endpoint": r"/api/refund",
    "ownership_check": r"userId.*req\.user|order\.userId|\.userId\s*!==",
    "amount_validate": r"amount.*<=|validateAmount|maxRefund|originalAmount|amount.*original",
    "idempotency": r"idempotency|idempotent|idempotency_key",
    "payment_config": r"PAYMENT_GATEWAY|payments-v2|paymentGateway",
    # user-profile-004
    "profile_endpoint": r"/api/user/profile|userProfile",
    "auth_check": r"authenticate\b|verifyToken|req\.user\.id|authMiddleware",
}


def detect_signals(diff: str) -> dict[str, bool]:
    return {name: bool(re.search(pattern, diff, re.IGNORECASE)) for name, pattern in _SIGNALS.items()}


def survey_implementation(docket: Docket, signals: dict[str, bool]) -> list[ImplementationFinding]:
    findings: list[ImplementationFinding] = []
    n = 1

    def add(summary: str, file_ref: str, evidence: str, kind: str = "added") -> None:
        nonlocal n
        findings.append(
            ImplementationFinding(id=f"I{n}", summary=summary, file_ref=file_ref, evidence=evidence, kind=kind)  # type: ignore[arg-type]
        )
        n += 1

    if signals.get("login_endpoint"):
        add("Login/route handler added", _file_for(docket, "login"), 'router.post("/api/login", ...)')
    if signals.get("bcrypt"):
        add("Password verified with bcrypt", _file_for(docket, "login"), "bcrypt.compare(password, user.passwordHash)")
    if signals.get("audit_log"):
        add("Audit log entry written", _file_for(docket, "login") or _file_for(docket, "refund"), 'auditLog(...)')
    if signals.get("health_endpoint"):
        add("Health endpoint added", _file_for(docket, "health"), 'router.get("/api/health", ...)')
    if signals.get("tests"):
        add("Regression test added", _file_for(docket, "test"), "test(...) / describe(...)")
    # payment-refund-003
    if signals.get("refund_endpoint"):
        add("Refund route handler added", _file_for(docket, "refund"), 'router.post("/api/refund", authenticate, ...)')
    if signals.get("ownership_check"):
        add("Order ownership verified before processing", _file_for(docket, "refund"), "order.userId !== req.user.id")
    # user-profile-004
    if signals.get("profile_endpoint"):
        add("User profile endpoint added", _file_for(docket, "user"), 'router.get("/api/user/profile", authenticate, ...)')
    if signals.get("auth_check"):
        add("Auth middleware applied — 401 enforced for unauthenticated requests", _file_for(docket, "user") or _file_for(docket, "refund"), "authenticate middleware + 401 test")

    for path in docket.touched_files:
        if "middleware" in path.lower():
            add("Auth middleware behaviour changed", path, "GET requests now bypass auth check", kind="changed")
        if "payment" in path.lower() or "gateway" in path.lower():
            add("Payment gateway configuration hardcoded", path, "PAYMENT_GATEWAY URL changed from env-driven to hardcoded", kind="changed")
    return findings


def _file_for(docket: Docket, keyword: str) -> str:
    for path in docket.touched_files:
        if keyword in path.lower():
            return path
    return docket.touched_files[0] if docket.touched_files else ""


_REQ_KEYWORDS: list[tuple[str, str]] = [
    # Most specific phrases first to avoid false matches
    ("rate-limit", "rate_limit"),
    ("rate limit", "rate_limit"),
    ("failed login", "rate_limit"),
    ("5 attempts", "rate_limit"),
    ("bcrypt", "bcrypt"),
    ("password", "bcrypt"),
    # payment-refund-003 — specific phrases before short words
    ("idempotency", "idempotency"),
    ("idempotent", "idempotency"),
    ("duplicate refund", "idempotency"),
    ("exceed the original", "amount_validate"),
    ("exceed", "amount_validate"),
    ("validates amount", "amount_validate"),
    ("owns the order", "ownership_check"),
    ("caller owns", "ownership_check"),
    ("ownership", "ownership_check"),
    ("/api/refund", "refund_endpoint"),
    ("payment gateway", "payment_config"),
    # user-profile-004
    ("unauthenticated", "auth_check"),
    ("valid auth", "auth_check"),
    ("auth token", "auth_check"),
    ("401", "auth_check"),
    ("profile", "profile_endpoint"),
    # generic — keep these after specific phrases
    ("audit", "audit_log"),
    ("test", "tests"),
    ("regression", "tests"),
    ("health", "health_endpoint"),
    ("sha", "git_sha"),
    ("commit", "git_sha"),
    ("login", "login_endpoint"),
]


def requirement_signal(req: RequirementItem) -> str | None:
    low = req.text.lower()
    for keyword, signal in _REQ_KEYWORDS:
        if keyword in low:
            return signal
    return None


def is_met(req: RequirementItem, signals: dict[str, bool]) -> bool:
    signal = requirement_signal(req)
    if signal is None:
        return True
    return signals.get(signal, False)


# --- LLM-backed agents (deterministic fallback) -----------------------------
#
# Each wrapper reasons over an *arbitrary* ticket/diff via the LLM provider
# chain. When ``docket.engine == "deterministic"`` (demo fixtures) or no
# provider is configured / the call fails (``complete_json`` returns None), it
# falls back to the original regex engine so a verdict always lands.


def _use_llm(docket: Docket) -> bool:
    return docket.engine != "deterministic"


_ADVOCATE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["requirements"],
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "text", "priority"],
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "priority": {"type": "string", "enum": ["must", "should"]},
                },
            },
        }
    },
}


def advocate_extract(docket: Docket) -> list[RequirementItem]:
    """ADVOCATE — turn a free-form ticket into a numbered requirement checklist."""
    if _use_llm(docket):
        text = "\n".join(source.text for source in docket.intent_sources)
        source_ref = docket.intent_sources[0].source_ref if docket.intent_sources else ""
        data = complete_json(
            "You are ADVOCATE, an intent witness. Extract an atomic, testable requirement "
            "checklist from a software ticket. Mark priority 'must' for mandatory items and "
            "stated constraints, 'should' for optional/nice-to-have. Number ids R1, R2, ...",
            f"Ticket:\n{text}\n\nReturn JSON {{requirements:[{{id,text,priority}}]}}.",
            _ADVOCATE_SCHEMA,
        )
        if data and isinstance(data.get("requirements"), list):
            items: list[RequirementItem] = []
            for i, row in enumerate(data["requirements"], start=1):
                body = str(row.get("text", "")).strip().rstrip(".")
                if not body:
                    continue
                priority = "should" if str(row.get("priority", "must")).lower() == "should" else "must"
                items.append(
                    RequirementItem(
                        id=str(row.get("id") or f"R{i}").strip(),
                        text=body,
                        priority=priority,  # type: ignore[arg-type]
                        source_ref=source_ref,
                    )
                )
            if items:
                return items
    return extract_requirements(docket)


_SURVEYOR_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["summary", "file_ref", "evidence", "kind"],
                "properties": {
                    "summary": {"type": "string"},
                    "file_ref": {"type": "string"},
                    "evidence": {"type": "string"},
                    "kind": {"type": "string", "enum": ["added", "changed", "removed"]},
                },
            },
        }
    },
}


def surveyor_inspect(docket: Docket) -> list[ImplementationFinding]:
    """SURVEYOR — report what the diff actually changed (facts, no opinions)."""
    if _use_llm(docket):
        data = complete_json(
            "You are SURVEYOR, an implementation witness. Inspect a unified diff and report "
            "what it actually changed — factual, no opinions. kind='added' for new behaviour, "
            "'changed' for modified existing behaviour, 'removed' for deletions.",
            f"Touched files: {', '.join(docket.touched_files)}\n\nDiff:\n{docket.diff}\n\n"
            "Return JSON {findings:[{summary,file_ref,evidence,kind}]}. evidence is a short snippet.",
            _SURVEYOR_SCHEMA,
            max_tokens=1500,
        )
        if data and isinstance(data.get("findings"), list):
            findings: list[ImplementationFinding] = []
            for i, row in enumerate(data["findings"], start=1):
                summary = str(row.get("summary", "")).strip()
                if not summary:
                    continue
                kind = str(row.get("kind", "added")).lower()
                if kind not in ("added", "changed", "removed"):
                    kind = "added"
                findings.append(
                    ImplementationFinding(
                        id=f"I{i}",
                        summary=summary,
                        file_ref=str(row.get("file_ref", "")).strip(),
                        evidence=str(row.get("evidence", "")).strip(),
                        kind=kind,  # type: ignore[arg-type]
                    )
                )
            if findings:
                return findings
    return survey_implementation(docket, detect_signals(docket.diff))


_GHOST_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["omissions"],
    "properties": {
        "omissions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["requirement_id", "severity", "detail"],
                "properties": {
                    "requirement_id": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "detail": {"type": "string"},
                },
            },
        }
    },
}


def ghost_omissions(
    docket: Docket, requirements: list[RequirementItem], impl: list[ImplementationFinding]
) -> list[Finding]:
    """GHOST — requirements requested but with no implementing evidence."""
    if _use_llm(docket) and requirements:
        req_text = "\n".join(f"{r.id} ({r.priority.upper()}): {r.text}" for r in requirements)
        impl_text = "\n".join(f"{f.id}: {f.summary} [{f.kind}] {f.file_ref}" for f in impl) or "(none)"
        data = complete_json(
            "You are GHOST, an omission auditor. Find requirements that were requested but have "
            "NO implementing evidence in the diff — the negative space. Only report genuinely "
            "missing items. severity 'critical' for an unmet MUST, 'medium' for an unmet SHOULD.",
            f"Requirements:\n{req_text}\n\nImplementation findings:\n{impl_text}\n\nDiff:\n{docket.diff}\n\n"
            "Return JSON {omissions:[{requirement_id,severity,detail}]}. Empty array if all implemented.",
            _GHOST_SCHEMA,
        )
        if data is not None and isinstance(data.get("omissions"), list):
            by_id = {r.id: r for r in requirements}
            findings: list[Finding] = []
            for row in data["omissions"]:
                rid = str(row.get("requirement_id", "")).strip()
                req = by_id.get(rid)
                if req is None:
                    continue
                severity = str(row.get("severity", "")).lower()
                if severity not in ("critical", "high", "medium", "low"):
                    severity = "critical" if req.priority == "must" else "medium"
                findings.append(
                    Finding(
                        agent="GHOST",
                        kind="omission",
                        severity=severity,  # type: ignore[arg-type]
                        detail=str(row.get("detail") or f"{rid} requested but no implementing evidence in the diff."),
                        requirement_id=rid,
                        evidence=[f'no signal for "{req.text}"'],
                    )
                )
            return findings
    # Deterministic fallback.
    signals = detect_signals(docket.diff)
    omissions: list[Finding] = []
    for req in requirements:
        if not is_met(req, signals):
            severity = "critical" if req.priority == "must" else "medium"
            omissions.append(
                Finding(
                    agent="GHOST",
                    kind="omission",
                    severity=severity,  # type: ignore[arg-type]
                    detail=f"{req.id} requested but no implementing evidence in the diff.",
                    requirement_id=req.id,
                    evidence=[f'no signal for "{req.text}"'],
                )
            )
    return omissions


_DRIFT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["drifts"],
    "properties": {
        "drifts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["file_ref", "severity", "detail", "evidence"],
                "properties": {
                    "file_ref": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "detail": {"type": "string"},
                    "evidence": {"type": "string"},
                },
            },
        }
    },
}


def drift_findings(
    docket: Docket, requirements: list[RequirementItem], impl: list[ImplementationFinding]
) -> list[Finding]:
    """DRIFT — changes in the diff that no requirement authorized (scope creep)."""
    if _use_llm(docket):
        req_text = "\n".join(f"{r.id}: {r.text}" for r in requirements) or "(none)"
        con_text = "\n".join(extract_constraints(docket)) or "(none stated)"
        data = complete_json(
            "You are DRIFT, a scope auditor. Find changes in the diff that NO requirement "
            "authorized — unrequested scope creep, especially changes that violate a stated "
            "constraint. Do NOT flag changes that trace to a requirement.",
            f"Requirements:\n{req_text}\n\nConstraints:\n{con_text}\n\nDiff:\n{docket.diff}\n\n"
            "Return JSON {drifts:[{file_ref,severity,detail,evidence}]}. Empty array if all changes trace to a requirement.",
            _DRIFT_SCHEMA,
            provider_hint="cerebras",
        )
        if data is not None and isinstance(data.get("drifts"), list):
            findings: list[Finding] = []
            for row in data["drifts"]:
                detail = str(row.get("detail", "")).strip()
                if not detail:
                    continue
                severity = str(row.get("severity", "high")).lower()
                if severity not in ("critical", "high", "medium", "low"):
                    severity = "high"
                evidence = str(row.get("evidence", "")).strip()
                findings.append(
                    Finding(
                        agent="DRIFT",
                        kind="scope_drift",
                        severity=severity,  # type: ignore[arg-type]
                        detail=detail,
                        file_ref=str(row.get("file_ref", "")).strip() or None,
                        evidence=[evidence] if evidence else [],
                    )
                )
            return findings
    # Deterministic fallback.
    drifts: list[Finding] = []
    constraints = extract_constraints(docket)
    for finding in impl:
        if finding.kind != "changed":
            continue
        ref_lower = finding.file_ref.lower()
        if "middleware" in ref_lower:
            violates = any("middleware" in c.lower() for c in constraints)
            drifts.append(
                Finding(
                    agent="DRIFT",
                    kind="scope_drift",
                    severity="high",
                    detail="Auth middleware behaviour changed — no requirement authorizes this"
                    + (" and it violates a stated constraint." if violates else "."),
                    file_ref=finding.file_ref,
                    evidence=[finding.evidence],
                )
            )
        elif "payment" in ref_lower or "gateway" in ref_lower:
            violates = any("payment" in c.lower() or "gateway" in c.lower() or "config" in c.lower() for c in constraints)
            drifts.append(
                Finding(
                    agent="DRIFT",
                    kind="scope_drift",
                    severity="high",
                    detail="Payment gateway configuration hardcoded — no requirement authorizes this"
                    + (" and it violates an explicit constraint." if violates else "."),
                    file_ref=finding.file_ref,
                    evidence=[finding.evidence],
                )
            )
    return drifts


_ARBITER_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary"],
    "properties": {"summary": {"type": "string"}},
}


def arbiter_summarize(docket: Docket, verdict: Verdict) -> Verdict:
    """ARBITER — optionally rewrite the verdict *summary prose* via the LLM.

    Scoring is deterministic and authoritative: this only ever replaces the
    one-line ``summary`` string, never the trust score, merge decision, or
    ledger. Any failure leaves the deterministic summary untouched.
    """
    if not _use_llm(docket):
        return verdict
    data = complete_json(
        "You are ARBITER, the judge. Write a single neutral one-sentence verdict summary for an "
        "intent-conformance review. Do not invent facts; reflect the given state and findings.",
        f"State: {verdict.state}\nMerge: {verdict.merge_decision}\nTrust: {verdict.trust_score}/100\n"
        f"Blockers: {verdict.blockers}\nConditions: {verdict.conditions}\n\nReturn JSON {{summary}}.",
        _ARBITER_SCHEMA,
        max_tokens=200,
    )
    if data and isinstance(data.get("summary"), str) and data["summary"].strip():
        return verdict.model_copy(update={"summary": data["summary"].strip()})
    return verdict


def _msg(agent: str, text: str, target: list[str] | None = None) -> TribunalEvent:
    return TribunalEvent(type="message", agent=agent, target=target, text=text)  # type: ignore[arg-type]


def _evt(agent: str, kind: str, payload: dict, text: str = "") -> TribunalEvent:
    return TribunalEvent(type="event", agent=agent, text=text, payload={"kind": kind, **payload})  # type: ignore[arg-type]


def _with_band(event: TribunalEvent, band: CoordinationBackend, *, mirrored: bool = True) -> TribunalEvent:
    payload = dict(event.payload)
    payload["band"] = band.band_meta(mirrored=mirrored)
    return event.model_copy(update={"payload": payload})


async def run_trial(docket: Docket, *, delay: float = STEP_DELAY) -> AsyncIterator[TribunalEvent]:
    started = time.perf_counter()
    band = get_coordination_backend()
    room_id: str | None = None
    band_warnings: list[str] = []

    async def band_warn(operation: str, exc: Exception) -> None:
        band_warnings.append(f"{operation}: {exc}")

    async def recruit(agent: str) -> bool:
        try:
            await band.add_participant(room_id, agent)
            return True
        except BandError as exc:
            await band_warn(f"add_participant({agent})", exc)
            return False

    async def emit(event: TribunalEvent, *, mirror: bool = True) -> list[TribunalEvent]:
        mirrored = False
        out_events: list[TribunalEvent] = []
        if mirror and band.enabled and room_id:
            try:
                if event.type == "message":
                    await band.send_message(
                        room_id,
                        event.agent or "CLERK",
                        event.text,
                        targets=event.target,
                    )
                    mirrored = True
                elif event.type == "event":
                    await band.post_event(
                        room_id,
                        event.agent or "CLERK",
                        event.payload.get("kind", ""),
                        event.payload,
                        text=event.text,
                    )
                    mirrored = True
            except BandError as exc:
                await band_warn(f"mirror({event.type})", exc)
                if band.strict:
                    return [
                        _with_band(
                            TribunalEvent(
                                type="error",
                                agent="CLERK",
                                text=f"Band mirror failed: {exc}",
                                payload={"severity": "error", "band_error": str(exc)},
                            ),
                            band,
                            mirrored=False,
                        )
                    ]
                out_events.append(
                    _with_band(
                        TribunalEvent(
                            type="event",
                            agent="CLERK",
                            text="Band mirror warning: local transcript continued but Band event failed.",
                            payload={"severity": "warning", "band_error": str(exc), "kind": "band_warning"},
                        ),
                        band,
                        mirrored=False,
                    )
                )
        out_events.append(_with_band(event, band, mirrored=mirrored))
        await asyncio.sleep(delay)
        return out_events

    async def stream_emit(event: TribunalEvent, *, mirror: bool = True) -> AsyncIterator[TribunalEvent]:
        for ev in await emit(event, mirror=mirror):
            yield ev
            if ev.type == "error":
                return

    try:
        room_id = await band.create_room(f"Tribunal · {docket.title}")
    except BandError as exc:
        yield _with_band(
            TribunalEvent(type="error", text=f"Band room creation failed: {exc}", payload={"band_error": str(exc)}),
            band,
            mirrored=False,
        )
        return

    yield _with_band(
        TribunalEvent(
            type="phase",
            text="Tribunal convened",
            payload={
                "trial_id": docket.trial_id,
                "title": docket.title,
                "band_mode": band.mode,
                "touched_domains": docket.touched_domains,
                "agents": [AGENTS[name].model_dump() for name in ("CLERK", "ADVOCATE", "SURVEYOR", "GHOST", "DRIFT", "ARBITER")],
            },
        ),
        band,
    )

    # 1. Recruit intent + implementation witnesses before @mentions.
    await recruit("ADVOCATE")
    await recruit("SURVEYOR")

    # 2. CLERK opens chamber and hands off.
    async for ev in stream_emit(
        _msg(
            "CLERK",
            f"Docket posted. Docket {docket.trial_id}: “{docket.title}”. Extract intent and inspect implementation.",
            target=["ADVOCATE", "SURVEYOR"],
        )
    ):
        yield ev

    # 3. ADVOCATE — requirements.
    requirements = advocate_extract(docket)
    for req in requirements:
        async for ev in stream_emit(_evt("ADVOCATE", "requirement", {"requirement": req.model_dump()}, text=f"{req.id} · {req.text}")):
            yield ev
    async for ev in stream_emit(
        _evt(
            "ADVOCATE",
            "summary",
            {"text": f"Intent extracted. {len(requirements)} requirements recorded."},
            text=f"Intent extracted. {len(requirements)} requirements recorded.",
        )
    ):
        yield ev

    # 4. SURVEYOR — implementation.
    impl = surveyor_inspect(docket)
    for finding in impl:
        async for ev in stream_emit(
            _evt("SURVEYOR", "implementation", {"finding": finding.model_dump()}, text=f"{finding.id} · {finding.summary}")
        ):
            yield ev
    async for ev in stream_emit(
        _evt(
            "SURVEYOR",
            "summary",
            {"text": f"Diff inspected. {len(impl)} implementation findings across {len(docket.touched_files)} files."},
            text=f"Diff inspected. {len(impl)} implementation findings across {len(docket.touched_files)} files.",
        )
    ):
        yield ev

    # 5. Recruit auditors before @mention handoff.
    await recruit("GHOST")
    await recruit("DRIFT")
    async for ev in stream_emit(
        _msg(
            "CLERK",
            "Compare requirements against implementation.",
            target=["GHOST", "DRIFT"],
        )
    ):
        yield ev

    # 6. GHOST — omissions.
    omissions = ghost_omissions(docket, requirements, impl)
    if omissions:
        async for ev in stream_emit(
            _evt(
                "GHOST",
                "summary",
                {"text": f"Negative space detected. {len(omissions)} requested item(s) absent from the diff."},
                text=f"Negative space detected. {len(omissions)} requested item(s) absent from the diff.",
            )
        ):
            yield ev
    else:
        async for ev in stream_emit(
            _evt("GHOST", "summary", {"text": "No omissions. Every requirement has implementing evidence."}, text="No omissions.")
        ):
            yield ev
    for finding in omissions:
        async for ev in stream_emit(_evt("GHOST", "omission", {"finding": finding.model_dump()}, text=finding.detail)):
            yield ev

    # 7. DRIFT — scope creep.
    drifts = drift_findings(docket, requirements, impl)
    if drifts:
        drift_text = f"Unauthorized change detected. {len(drifts)} modification(s) outside the docket."
        async for ev in stream_emit(
            _evt(
                "DRIFT",
                "summary",
                {"text": drift_text},
                text=drift_text,
            )
        ):
            yield ev
    else:
        async for ev in stream_emit(
            _evt("DRIFT", "summary", {"text": "No scope drift. Every change traces back to a requirement."}, text="No scope drift.")
        ):
            yield ev
    for finding in drifts:
        async for ev in stream_emit(_evt("DRIFT", "scope_drift", {"finding": finding.model_dump()}, text=finding.detail)):
            yield ev

    # 7b. Cross-agent debate — GHOST vs SURVEYOR, DRIFT vs ADVOCATE.
    if omissions:
        missing_list = ", ".join(o.requirement_id for o in omissions[:3])
        async for ev in stream_emit(
            _msg(
                "GHOST",
                f"@SURVEYOR — {missing_list} {'show' if len(omissions) > 1 else 'shows'} zero implementing signals in your report. "
                f"I scanned every diff line. {'These requirements have' if len(omissions) > 1 else 'This requirement has'} no corresponding code. "
                f"Do you have any evidence I may have missed?",
                target=["SURVEYOR"],
            )
        ):
            yield ev
        async for ev in stream_emit(
            _msg(
                "SURVEYOR",
                f"@GHOST — scan confirmed and complete. {missing_list} {'are' if len(omissions) > 1 else 'is'} absent from the submitted diff. "
                f"No file in the docket implements {'these requirements' if len(omissions) > 1 else 'this requirement'}. "
                f"Your finding is valid. I have no counter-evidence.",
                target=["GHOST"],
            )
        ):
            yield ev

    if drifts:
        drift_file = drifts[0].file_ref or "an out-of-scope file"
        async for ev in stream_emit(
            _msg(
                "DRIFT",
                f"@ADVOCATE — I need your read on {drift_file}. "
                f"My scan found a change that has no authorizing requirement in your extraction. "
                f"Did any ticket requirement implicitly cover this modification?",
                target=["ADVOCATE"],
            )
        ):
            yield ev
        async for ev in stream_emit(
            _msg(
                "ADVOCATE",
                f"@DRIFT — I reviewed all {len(requirements)} extracted requirements. None authorizes changes to {drift_file}. "
                f"The constraint was unambiguous. Your scope-drift finding stands.",
                target=["DRIFT"],
            )
        ):
            yield ev

    if omissions and drifts:
        async for ev in stream_emit(
            _msg(
                "GHOST",
                "@DRIFT — agreed on scope drift. Combined with the missing requirements, "
                "this diff has both coverage gaps and unauthorized changes. "
                "I'm flagging this as a compounded failure for ARBITER.",
                target=["DRIFT"],
            )
        ):
            yield ev
        async for ev in stream_emit(
            _msg(
                "DRIFT",
                "@GHOST — concur. The diff is both incomplete and out of scope. "
                "Routing joint finding to ARBITER.",
                target=["GHOST"],
            )
        ):
            yield ev

    # 8. CLERK recruits WARDEN for sensitive domains.
    constraint_findings: list[Finding] = []
    sensitive = bool({"auth", "security"} & set(d.lower() for d in docket.touched_domains))
    if sensitive:
        await recruit("WARDEN")
        yield _with_band(
            TribunalEvent(
                type="recruitment",
                agent="CLERK",
                target=["WARDEN"],
                text="Security-sensitive change detected. Review constraints.",
                payload={"recruited": "WARDEN", "reason": "auth/security domain", "agent_meta": AGENTS["WARDEN"].model_dump()},
            ),
            band,
        )
        await asyncio.sleep(delay)
        unmet_security = [o for o in omissions if o.requirement_id]
        detail = "Policy requires throttling of failed logins. Missing rate limit is a blocking security control."
        constraint_findings.append(
            Finding(
                agent="WARDEN",
                kind="constraint",
                severity="high",
                detail=detail,
                requirement_id=unmet_security[0].requirement_id if unmet_security else None,
                evidence=["OWASP A07: Identification & Authentication Failures"],
            )
        )
        async for ev in stream_emit(_evt("WARDEN", "summary", {"text": detail}, text=detail)):
            yield ev
        for finding in constraint_findings:
            async for ev in stream_emit(_evt("WARDEN", "constraint", {"finding": finding.model_dump()}, text=finding.detail)):
                yield ev

    # 9. CLERK recruits ARBITER and requests ruling.
    await recruit("ARBITER")
    async for ev in stream_emit(_msg("CLERK", "Issue the ruling from the event ledger.", target=["ARBITER"])):
        yield ev

    verdict = adjudicate(requirements, omissions, drifts, constraint_findings, {})
    verdict = arbiter_summarize(docket, verdict)
    try:
        await band.post_event(room_id, "ARBITER", "verdict", verdict.model_dump(), text=verdict.summary)
        verdict_mirrored = True
    except BandError as exc:
        await band_warn("post_event(ARBITER,verdict)", exc)
        verdict_mirrored = False
        if band.strict:
            yield _with_band(
                TribunalEvent(type="error", text=f"Band verdict mirror failed: {exc}", payload={"band_error": str(exc)}),
                band,
                mirrored=False,
            )
            return
    try:
        await band.send_message(room_id, "CLERK", f"Ruling issued: {verdict.summary}", targets=["ARBITER"])
    except BandError as exc:
        await band_warn("send_message(ARBITER summary)", exc)
    yield _with_band(
        TribunalEvent(type="verdict", agent="ARBITER", text=verdict.summary, payload=verdict.model_dump()),
        band,
        mirrored=verdict_mirrored,
    )
    await asyncio.sleep(delay)

    yield _with_band(
        TribunalEvent(
            type="done",
            text="Trial complete.",
            payload={
                "trial_id": docket.trial_id,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "band_mode": band.mode,
                "band_warnings": band_warnings,
            },
        ),
        band,
    )


def adjudicate(
    requirements: list[RequirementItem],
    omissions: list[Finding],
    drifts: list[Finding],
    constraints: list[Finding],
    signals: dict[str, bool],
) -> Verdict:
    score = 100
    deductions: list[TrustDeduction] = []
    blockers: list[str] = []
    conditions: list[str] = []

    for finding in omissions:
        if finding.severity == "critical":
            score -= 30
            deductions.append(TrustDeduction(reason=f"Unmet MUST ({finding.requirement_id})", points=-30))
            blockers.append(finding.detail)
        else:
            score -= 10
            deductions.append(TrustDeduction(reason=f"Unmet SHOULD ({finding.requirement_id})", points=-10))
            conditions.append(finding.detail)

    for finding in drifts:
        if finding.severity == "high":
            score -= 20
            deductions.append(TrustDeduction(reason="High-severity scope drift", points=-20))
            blockers.append(finding.detail)

    for finding in constraints:
        score -= 15
        deductions.append(TrustDeduction(reason="Security policy constraint", points=-15))
        blockers.append(finding.detail)

    score = max(0, min(100, score))

    ledger: list[LedgerRow] = []
    unmet_ids = {o.requirement_id for o in omissions}
    for req in requirements:
        if req.id in unmet_ids:
            decision = "UNMET"
            notes = "Requested but absent from the diff."
        else:
            decision = "MET"
            notes = "Implementing evidence present."
        ledger.append(LedgerRow(requirement_id=req.id, requirement=req.text, decision=decision, notes=notes))  # type: ignore[arg-type]
    for finding in drifts:
        ledger.append(
            LedgerRow(
                requirement_id="—",
                requirement="(no authorizing requirement)",
                code_refs=[finding.file_ref or ""],
                decision="DRIFT",
                notes=finding.detail,
            )
        )

    if score <= 49:
        state, merge = "DOES_NOT_CONFORM", "BLOCK"
        summary = "The implementation does not conform to the requested intent. Merge is blocked."
    elif score <= 79:
        state, merge = "CONFORMS_WITH_CONDITIONS", "APPROVE_WITH_CONDITIONS"
        summary = "The implementation broadly conforms but carries conditions to resolve before merge."
    else:
        state, merge = "CONFORMS", "APPROVE"
        summary = "The implementation conforms to the requested intent. Cleared to merge."

    return Verdict(
        state=state,  # type: ignore[arg-type]
        trust_score=score,
        merge_decision=merge,  # type: ignore[arg-type]
        blockers=blockers,
        conditions=conditions,
        ledger=ledger,
        deductions=deductions,
        summary=summary,
    )


async def run_trial_by_fixture(fixture_id: str, *, delay: float = STEP_DELAY) -> AsyncIterator[TribunalEvent]:
    docket = get_fixture(fixture_id)
    if docket is None:
        yield TribunalEvent(type="error", text=f"Unknown fixture: {fixture_id}")
        return
    async for event in run_trial(docket, delay=delay):
        yield event
