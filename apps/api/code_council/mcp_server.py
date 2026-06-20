"""Tribunal MCP server — exposes intent-conformance review as MCP tools.

This is the autonomous-loop delivery layer. Instead of a human opening the War
Room and clicking "Convene Tribunal", an AI coding agent (Claude Code, Cursor,
…) connects to this MCP server and calls these tools directly: before a human
ever sees the diff, the agent can ask "does this match the ticket?" and, on a
BLOCK verdict, loop to fix omissions and scope drift itself.

Tools
-----
- ``verify_intent_conformance``  full court — Trust Score + traceability ledger
  (mirrors into a live Band room exactly like the UI does).
- ``ghost_check``  fast: requested-but-missing requirements only.
- ``drift_check``  fast: changes with no authorizing requirement only.

Run (stdio):
    tribunal-mcp           # installed console script
    python -m code_council.mcp_server

Register in Claude Code / Cursor MCP config (clone-free via uvx)::

    {
      "mcpServers": {
        "tribunal": {
          "command": "uvx",
          "args": ["--from", "code-tribunal", "tribunal-mcp"],
          "env": { "GROQ_API_KEY": "<your key>" }
        }
      }
    }

Codex (~/.codex/config.toml)::

    [mcp_servers.tribunal]
    command = "uvx"
    args = ["--from", "code-tribunal", "tribunal-mcp"]
    env = { GROQ_API_KEY = "<your key>" }
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .tribunal.headless import (
    build_adhoc_docket,
    drift_check_docket,
    ghost_check_docket,
    run_trial_collect,
    summarize_verdict,
)

mcp = FastMCP("tribunal")


@mcp.tool()
async def verify_intent_conformance(
    ticket_description: str,
    git_diff: str,
    touched_domains: list[str] | None = None,
) -> dict:
    """Adjudicate whether a diff conforms to the original request.

    Convenes the full Tribunal (CLERK → ADVOCATE/SURVEYOR → GHOST/DRIFT →
    WARDEN if security-sensitive → ARBITER) over the supplied ticket and diff,
    mirroring the deliberation into a live Band room when configured.

    Args:
        ticket_description: The original task/ticket text. Number requirements
            as ``R1 (MUST): ...`` / ``R2 (SHOULD): ...`` and add
            ``Constraint: ...`` lines for the strongest signal.
        git_diff: The unified diff the coding agent produced.
        touched_domains: Optional domain hints (e.g. ["auth", "payments"]);
            auth/security are also auto-detected from the diff.

    Returns:
        Structured result with ``verdict`` (state, trust_score, merge_decision,
        blockers, conditions, ledger, deductions), a one-line ``headline``,
        the agents ``recruited``, structured ``findings``, and ``band_mode``.
        Treat ``merge_decision == "BLOCK"`` as a signal to loop and fix.
    """
    docket = build_adhoc_docket(ticket_description, git_diff, touched_domains)
    result = await run_trial_collect(docket)
    result["headline"] = summarize_verdict(result.get("verdict"))
    return result


@mcp.tool()
def ghost_check(ticket_description: str, git_diff: str) -> dict:
    """Fast omission pre-check — requested work that is missing from the diff.

    Call this mid-generation to ask "did I miss any requirements yet?" without
    convening the whole court. Deterministic and fast (no Band round-trip).

    Returns:
        ``{"missing": [...], "count": N, "conforms": bool}`` where each missing
        entry has requirement_id, requirement, priority, and severity.
    """
    docket = build_adhoc_docket(ticket_description, git_diff)
    missing = ghost_check_docket(docket)
    return {"missing": missing, "count": len(missing), "conforms": not missing}


@mcp.tool()
def drift_check(ticket_description: str, git_diff: str) -> dict:
    """Fast scope-drift pre-check — changes no requirement authorized.

    Call this to ask "did I change something I shouldn't have?". Deterministic
    and fast.

    Returns:
        ``{"drifts": [...], "count": N, "in_scope": bool}`` where each drift
        entry has file_ref, summary, and evidence.
    """
    docket = build_adhoc_docket(ticket_description, git_diff)
    drifts = drift_check_docket(docket)
    return {"drifts": drifts, "count": len(drifts), "in_scope": not drifts}


def main() -> None:
    # Load a local gitignored .env so a self-hosted `tribunal-mcp` finds keys
    # without exporting them; an MCP client `env` block still takes precedence.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:  # pragma: no cover - dotenv is a hard dep, but stay safe
        pass
    mcp.run()


if __name__ == "__main__":
    main()
