---
name: code-tribunal-gate
description: Gate code changes against the original ticket before declaring work done. Use whenever you have written or modified code to satisfy a request — call the Tribunal MCP tools (ghost_check, drift_check, verify_intent_conformance) to confirm the diff builds what was actually asked, and loop to fix any BLOCK before finishing.
---

# Code Tribunal gate

Code Tribunal is an intent-conformance reviewer. It does not ask "is this code good?" — it
asks "did this diff build what the ticket actually asked for?" Use it as a self-imposed gate
before you commit, push, or report a task complete.

This skill assumes the `tribunal` MCP server is configured (see `../config.yaml`). It exposes
three tools.

## When to use

After you have produced a diff for a request and before you declare it done. Also useful
mid-generation to catch problems early.

## Procedure

1. **Gather inputs.** You need two strings:
   - `ticket` — the original request. Number requirements as `R1 (MUST): …`, `R2 (SHOULD): …`
     and add `Constraint: …` lines for the strongest signal.
   - `git_diff` — the unified diff of your changes (e.g. `git diff HEAD`).

2. **Fast pre-checks (cheap, deterministic — run these often).**
   - Call `ghost_check(ticket, git_diff)`. If `conforms` is false, you have left requested work
     unimplemented — implement the listed `missing` items, then re-run.
   - Call `drift_check(ticket, git_diff)`. If `in_scope` is false, you changed something no
     requirement authorized — remove or justify each `drifts` entry, then re-run.

3. **Full adjudication (before finishing).**
   - Call `verify_intent_conformance(ticket, git_diff)`.
   - Read `verdict.merge_decision`:
     - `APPROVE` / `APPROVE_WITH_CONDITIONS` → you may finish. Address any `conditions` first.
     - `BLOCK` → **you are not done.** Fix every entry in `verdict.blockers`, regenerate the
       diff, and return to step 2. Do not report success on a BLOCK.

4. **Report.** When clear, summarize the final verdict: trust score, merge decision, and any
   conditions you satisfied. Cite `verdict.ledger` to show each requirement was traced.

## Cost notes

`ghost_check` and `drift_check` are deterministic and cheap — call them liberally. Reserve
`verify_intent_conformance` (the full court) for the final gate or when the fast checks pass but
you want the trust score and ledger.
