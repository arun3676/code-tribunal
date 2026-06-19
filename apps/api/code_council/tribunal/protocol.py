"""Tribunal protocol schemas + agent roster.

These types are the stable contract between the runner, the SSE endpoint,
and the War Room UI. Keep field names in sync with
``apps/web/src/lib/api.ts``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# --- Agent roster -----------------------------------------------------------

AgentName = Literal[
    "CLERK",
    "ADVOCATE",
    "SURVEYOR",
    "GHOST",
    "DRIFT",
    "WARDEN",
    "ARBITER",
]


class AgentMeta(BaseModel):
    """Static persona metadata surfaced to the UI for badges + avatars."""

    name: AgentName
    role: str
    provider: str
    color: str
    summary: str
    recruited: bool = False


# Persona colors mirror apps/web globals.css (--clerk, --advocate, ...).
AGENTS: dict[str, AgentMeta] = {
    "CLERK": AgentMeta(
        name="CLERK",
        role="Orchestrator",
        provider="Band",
        color="#66ccff",
        summary="Opens the chamber, routes @mentions, recruits specialists.",
    ),
    "ADVOCATE": AgentMeta(
        name="ADVOCATE",
        role="Intent Witness",
        provider="AI/ML API",
        color="#ffaa44",
        summary="Extracts the requirement checklist from the ticket.",
    ),
    "SURVEYOR": AgentMeta(
        name="SURVEYOR",
        role="Implementation Witness",
        provider="Code Council",
        color="#00ff66",
        summary="Inspects what the diff actually changed.",
    ),
    "GHOST": AgentMeta(
        name="GHOST",
        role="Omission Auditor",
        provider="AI/ML API",
        color="#c3c6e0",
        summary="Finds requested work that is absent — negative space.",
    ),
    "DRIFT": AgentMeta(
        name="DRIFT",
        role="Scope Auditor",
        provider="Featherless",
        color="#b07cff",
        summary="Finds changes no requirement authorized.",
    ),
    "WARDEN": AgentMeta(
        name="WARDEN",
        role="Constraint Witness",
        provider="Band recruited",
        color="#ff5577",
        summary="Security/policy witness recruited for sensitive domains.",
        recruited=True,
    ),
    "ARBITER": AgentMeta(
        name="ARBITER",
        role="Judge",
        provider="AI/ML API",
        color="#f5c542",
        summary="Issues the verdict, trust score, and traceability ledger.",
    ),
}


# --- Docket (input) ---------------------------------------------------------


class IntentSource(BaseModel):
    source_ref: str
    title: str
    text: str


class Docket(BaseModel):
    trial_id: str
    title: str
    intent_sources: list[IntentSource] = Field(default_factory=list)
    diff: str = ""
    touched_files: list[str] = Field(default_factory=list)
    touched_domains: list[str] = Field(default_factory=list)


# --- Findings (mid-trial) ---------------------------------------------------

Priority = Literal["must", "should"]
Severity = Literal["critical", "high", "medium", "low"]
FindingKind = Literal["omission", "scope_drift", "constraint"]
LedgerDecision = Literal["MET", "PARTIAL", "UNMET", "DRIFT", "CONDITION"]


class RequirementItem(BaseModel):
    id: str  # R1, R2, ...
    text: str
    priority: Priority = "must"
    source_ref: str = ""


class ImplementationFinding(BaseModel):
    id: str  # I1, I2, ...
    summary: str
    file_ref: str = ""
    evidence: str = ""
    kind: Literal["added", "changed", "removed"] = "added"


class Finding(BaseModel):
    agent: AgentName
    kind: FindingKind
    severity: Severity
    detail: str
    requirement_id: str | None = None
    file_ref: str | None = None
    evidence: list[str] = Field(default_factory=list)


# --- Verdict (output) -------------------------------------------------------

VerdictState = Literal[
    "CONFORMS",
    "CONFORMS_WITH_CONDITIONS",
    "DOES_NOT_CONFORM",
]
MergeDecision = Literal["APPROVE", "APPROVE_WITH_CONDITIONS", "BLOCK"]


class LedgerRow(BaseModel):
    requirement_id: str
    requirement: str
    code_refs: list[str] = Field(default_factory=list)
    decision: LedgerDecision
    notes: str = ""


class TrustDeduction(BaseModel):
    reason: str
    points: int


class Verdict(BaseModel):
    state: VerdictState
    trust_score: int
    merge_decision: MergeDecision
    blockers: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    ledger: list[LedgerRow] = Field(default_factory=list)
    deductions: list[TrustDeduction] = Field(default_factory=list)
    summary: str = ""


# --- Stream envelope --------------------------------------------------------

TribunalEventType = Literal[
    "phase",
    "message",
    "event",
    "recruitment",
    "verdict",
    "done",
    "error",
]


class TribunalEvent(BaseModel):
    type: TribunalEventType
    agent: AgentName | None = None
    target: list[AgentName] | None = None
    text: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
