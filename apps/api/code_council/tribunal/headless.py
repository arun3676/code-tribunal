"""Headless Tribunal entrypoints — shared by the SSE endpoint, the JSON
verdict endpoint, the MCP server, and the GitHub webhook.

The War Room UI consumes the streaming ``run_trial`` generator. Programmatic
callers (coding agents, CI, MCP clients) only want the final verdict and a
compact transcript, with no SSE plumbing. ``run_trial_collect`` drains the same
generator headlessly (zero pacing delay) so there is exactly one source of
truth for the trial logic.
"""

from __future__ import annotations

import re
import time

from .protocol import Docket, IntentSource, Verdict
from .runner import (
    advocate_extract,
    drift_findings,
    ghost_omissions,
    requirement_signal,
    run_trial,
    surveyor_inspect,
)

# --- Docket construction (shared with server.py) ----------------------------

_DIFF_FILE_RE = re.compile(r"[+]{3}\s+b/(\S+)")


def detect_domains(diff: str, declared: list[str] | None = None) -> list[str]:
    """Infer touched domains from the diff so WARDEN recruitment fires.

    Mirrors the original server-side heuristic; centralized here so every
    caller (SSE, JSON, MCP, webhook) classifies domains identically.
    """
    domains = {d.strip().lower() for d in (declared or []) if d.strip()}
    text = diff.lower()
    if any(k in text for k in ("login", "auth", "password", "token", "session")):
        domains.add("auth")
    if any(k in text for k in ("bcrypt", "crypto", "secret", "middleware", "permission")):
        domains.add("security")
    return sorted(domains)


def build_adhoc_docket(
    ticket: str,
    diff: str,
    touched_domains: list[str] | None = None,
    title: str | None = None,
) -> Docket:
    """Build a Docket from a raw ticket + unified diff (no fixture)."""
    files = sorted({m for m in _DIFF_FILE_RE.findall(diff)})
    return Docket(
        trial_id=f"adhoc-{int(time.time())}",
        title=title or "Ad-hoc tribunal",
        intent_sources=[IntentSource(source_ref="custom", title="Ticket", text=ticket)],
        diff=diff,
        touched_files=files,
        touched_domains=detect_domains(diff, touched_domains),
    )


# --- Headless trial collection ----------------------------------------------


async def run_trial_collect(docket: Docket) -> dict:
    """Run a full trial headlessly and return the structured result.

    Drains the canonical ``run_trial`` generator (so Band mirroring, WARDEN
    recruitment, and adjudication all happen exactly as in the UI) but returns
    a single JSON-serializable dict instead of an SSE stream.
    """
    started = time.perf_counter()
    verdict: dict | None = None
    transcript: list[dict] = []
    findings: list[dict] = []
    recruited: list[str] = []
    band_mode = "demo"
    error: str | None = None

    async for ev in run_trial(docket, delay=0.0):
        if ev.type == "phase":
            band_mode = ev.payload.get("band_mode", band_mode)
        elif ev.type == "message" and ev.agent:
            transcript.append({"agent": ev.agent, "text": ev.text, "target": ev.target})
        elif ev.type == "recruitment":
            who = ev.payload.get("recruited")
            if who:
                recruited.append(who)
        elif ev.type == "event":
            kind = ev.payload.get("kind")
            if kind in ("omission", "scope_drift", "constraint"):
                finding = ev.payload.get("finding", {})
                findings.append(
                    {
                        "agent": ev.agent,
                        "kind": kind,
                        "severity": finding.get("severity"),
                        "detail": finding.get("detail", ev.text),
                        "requirement_id": finding.get("requirement_id"),
                        "file_ref": finding.get("file_ref"),
                    }
                )
        elif ev.type == "verdict":
            verdict = ev.payload
        elif ev.type == "done":
            band_mode = ev.payload.get("band_mode", band_mode)
        elif ev.type == "error":
            error = ev.text

    return {
        "trial_id": docket.trial_id,
        "title": docket.title,
        "band_mode": band_mode,
        "touched_domains": docket.touched_domains,
        "recruited": recruited,
        "findings": findings,
        "transcript": transcript,
        "verdict": verdict,
        "error": error,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
    }


# --- Standalone pre-checks (GHOST / DRIFT money-makers) ----------------------
#
# These let a coding agent ping a single auditor mid-generation without
# convening the whole court — "did I miss a requirement yet?" / "did I change
# something I shouldn't have?". Deterministic, fast, no Band round-trip.


def ghost_check_docket(docket: Docket) -> list[dict]:
    """Return requested-but-missing requirements (GHOST's negative space).

    Uses the LLM-backed agents (deterministic fallback) so it works on real,
    free-form tickets/diffs — not just numbered fixtures.
    """
    requirements = advocate_extract(docket)
    by_id = {req.id: req for req in requirements}
    missing: list[dict] = []
    for finding in ghost_omissions(docket, requirements, []):
        req = by_id.get(finding.requirement_id or "")
        missing.append(
            {
                "requirement_id": finding.requirement_id,
                "requirement": req.text if req else finding.detail,
                "priority": req.priority if req else ("must" if finding.severity == "critical" else "should"),
                "severity": finding.severity,
                "signal": requirement_signal(req) if req else None,
            }
        )
    return missing


def drift_check_docket(docket: Docket) -> list[dict]:
    """Return changes with no authorizing requirement (DRIFT's scope creep)."""
    requirements = advocate_extract(docket)
    impl = surveyor_inspect(docket)
    drifts: list[dict] = []
    for finding in drift_findings(docket, requirements, impl):
        drifts.append(
            {
                "file_ref": finding.file_ref or "",
                "summary": finding.detail,
                "evidence": "; ".join(finding.evidence),
            }
        )
    return drifts


def summarize_verdict(verdict: dict | None) -> str:
    """One-line human/agent-readable headline for a verdict dict."""
    if not verdict:
        return "No verdict produced."
    return (
        f"{verdict.get('state')} · merge={verdict.get('merge_decision')} · "
        f"trust={verdict.get('trust_score')}/100 · "
        f"{len(verdict.get('blockers', []))} blocker(s), "
        f"{len(verdict.get('conditions', []))} condition(s)"
    )


__all__ = [
    "build_adhoc_docket",
    "detect_domains",
    "run_trial_collect",
    "ghost_check_docket",
    "drift_check_docket",
    "summarize_verdict",
    "Verdict",
]
