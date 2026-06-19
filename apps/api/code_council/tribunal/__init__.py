"""Code Council Tribunal — Band-powered intent-conformance review.

This package adds a multi-agent "court" on top of Code Council. A trial
reconciles the original ticket/spec (intent) against the actual diff
(implementation) and streams a Band-style deliberation over SSE.

Public surface:
- protocol: Pydantic schemas + agent roster
- fixtures: demo dockets (the "money" auth-login case)
- runner: ``run_trial(docket)`` async generator of TribunalEvent
- band_adapter: optional real Band room mirroring (enabled/disabled modes)
"""

from .protocol import (
    AGENTS,
    Docket,
    Finding,
    LedgerRow,
    RequirementItem,
    TribunalEvent,
    Verdict,
)
from .runner import run_trial

__all__ = [
    "AGENTS",
    "Docket",
    "Finding",
    "LedgerRow",
    "RequirementItem",
    "TribunalEvent",
    "Verdict",
    "run_trial",
]
