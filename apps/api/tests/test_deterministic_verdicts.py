"""Regression tests for the zero-key deterministic engine's honesty.

The offline engine must never silently APPROVE what it cannot verify, and a
verdict must never read APPROVE while blockers exist.
"""

from __future__ import annotations

import asyncio

from code_council.tribunal.protocol import Finding, RequirementItem
from code_council.tribunal.runner import (
    adjudicate,
    detect_signals,
    ghost_omissions,
    is_met,
)
from code_council.tribunal.headless import build_adhoc_docket, run_trial_collect


TICKET = (
    "Add rate limiting to the login endpoint.\n"
    "R1 (MUST): Limit failed logins to 5 attempts per 15 minutes.\n"
    "R2 (MUST): Return 429 with a Retry-After header.\n"
)

LOGGING_ONLY_DIFF = """\
diff --git a/auth/login.py b/auth/login.py
--- a/auth/login.py
+++ b/auth/login.py
@@ -1,4 +1,6 @@
 def login(request):
+    logger.info("login attempt from %s", request.ip)
     return handle_login(request)
"""


def test_logging_only_diff_does_not_satisfy_rate_limit() -> None:
    # "attempt" in a log line must not count as implementing rate limiting.
    signals = detect_signals(LOGGING_ONLY_DIFF)
    assert signals["rate_limit"] is False


def test_unmapped_requirement_is_unverified_not_met() -> None:
    req = RequirementItem(
        id="R9",
        text="Support quantum-safe key exchange on the websocket layer",
        priority="must",
        source_ref="ticket",
    )
    assert is_met(req, detect_signals(LOGGING_ONLY_DIFF)) is None


def test_offline_verify_blocks_logging_only_diff() -> None:
    docket = build_adhoc_docket(title="rate limit", ticket=TICKET, diff=LOGGING_ONLY_DIFF)
    result = asyncio.run(run_trial_collect(docket))
    verdict = result["verdict"]
    # The unmet rate-limit MUST is a blocker; blockers force BLOCK even when
    # the arithmetic lands above the 49-point threshold.
    assert verdict["merge_decision"] == "BLOCK"
    assert verdict["state"] == "DOES_NOT_CONFORM"
    assert verdict["trust_score"] < 80


def test_unverified_requirements_surface_as_conditions() -> None:
    ticket = (
        "R1 (MUST): Support quantum-safe key exchange on the websocket layer.\n"
    )
    docket = build_adhoc_docket(title="unverifiable", ticket=ticket, diff=LOGGING_ONLY_DIFF)
    result = asyncio.run(run_trial_collect(docket))
    verdict = result["verdict"]
    # Never a clean 100/APPROVE for something the engine could not check.
    assert verdict["trust_score"] < 100
    ledger_decisions = {row["requirement_id"]: row["decision"] for row in verdict["ledger"]}
    assert ledger_decisions.get("R1") == "CONDITION"
    assert any("could not be verified" in c for c in verdict["conditions"])


def test_blockers_always_mean_block() -> None:
    requirements = [
        RequirementItem(id="R1", text="Rate-limit failed logins", priority="must", source_ref="t")
    ]
    constraint = Finding(
        agent="WARDEN",
        kind="constraint",
        severity="critical",
        detail="Missing rate limit is a blocking security control.",
        requirement_id="R1",
    )
    verdict = adjudicate(requirements, [], [], [constraint], {})
    # One -15 constraint leaves score 85, but the blocker must force BLOCK.
    assert verdict.blockers
    assert verdict.merge_decision == "BLOCK"
    assert verdict.state == "DOES_NOT_CONFORM"
