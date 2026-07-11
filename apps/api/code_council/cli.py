"""Command-line interface for Code Tribunal.

Wraps the same headless engine the MCP server and web API use, for CI gating and
local checks. The ``verify`` command exits non-zero on a BLOCK verdict so it can
be dropped straight into a pipeline:

    tribunal verify --ticket ticket.md --diff pr.diff || exit 1

Subcommands:
    verify   full court — trust score, merge decision, blockers, ledger
    ghost    fast omission pre-check (requested-but-missing requirements)
    drift    fast scope-drift pre-check (changes no requirement authorized)
    init     print the MCP wiring block for an agent (openclaw, hermes, …)
    doctor   check that your BYO provider keys (Groq/Cerebras/Gemini) work
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys

from .agent_config import (
    SUPPORTED_AGENTS,
    config_target_path,
    render_agent_config,
    writable_config_path,
)
from .tribunal import llm as tribunal_llm
from .tribunal.headless import (
    build_adhoc_docket,
    drift_check_docket,
    ghost_check_docket,
    run_trial_collect,
    summarize_verdict,
)

# Exit codes: 0 = clear to merge, 1 = blocked / problems found / error.
EXIT_OK = 0
EXIT_BLOCK = 1

_APPROVE_DECISIONS = {"APPROVE", "APPROVE_WITH_CONDITIONS"}


def _read_source(value: str) -> str:
    """Read a ticket/diff argument: ``-`` means stdin, else a file path."""

    if value == "-":
        return sys.stdin.read()
    with open(value, "r", encoding="utf-8") as handle:
        return handle.read()


def _split_domains(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _resolve_diff(args: argparse.Namespace) -> str:
    """Resolve the diff from ``--diff`` (file/stdin) or ``--git`` (run git diff).

    ``--git`` makes the CLI agent-friendly: an AI agent can verify its own
    uncommitted work in one call without capturing the diff itself.
    ``--git`` with no value diffs against HEAD (all uncommitted changes);
    ``--git <ref>`` diffs against that ref.
    """

    git_ref = getattr(args, "git", None)
    if git_ref is not None:
        proc = subprocess.run(
            ["git", "diff", git_ref],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            # git's stderr can be a full 150-line usage screen — keep line one.
            stderr_lines = (proc.stderr or "").strip().splitlines()
            raise RuntimeError(stderr_lines[0] if stderr_lines else "git diff failed")
        return proc.stdout
    return _read_source(args.diff)


def _empty_diff_exit(args: argparse.Namespace) -> int:
    """Empty diff = nothing to review — a clean pass, not a silent 30s trial."""
    if getattr(args, "json", False):
        print(json.dumps({"empty_diff": True, "merge_decision": "APPROVE"}, indent=2))
    elif not getattr(args, "quiet", False):
        print("empty diff — nothing to review; clear to merge")
    return EXIT_OK


def _cmd_verify(args: argparse.Namespace) -> int:
    ticket = _read_source(args.ticket)
    diff = _resolve_diff(args)
    if not diff.strip():
        return _empty_diff_exit(args)
    docket = build_adhoc_docket(ticket, diff, _split_domains(args.domains), args.title)
    result = asyncio.run(run_trial_collect(docket))
    result["headline"] = summarize_verdict(result.get("verdict"))

    if args.json:
        print(json.dumps(result, indent=2))
    elif not getattr(args, "quiet", False):
        _print_verdict(result)

    verdict = result.get("verdict") or {}
    if result.get("error"):
        return EXIT_BLOCK
    return EXIT_OK if verdict.get("merge_decision") in _APPROVE_DECISIONS else EXIT_BLOCK


def _print_verdict(result: dict) -> None:
    verdict = result.get("verdict")
    if not verdict:
        print(f"No verdict produced. {result.get('error') or ''}".strip(), file=sys.stderr)
        return
    print(summarize_verdict(verdict))
    print()
    print(f"  state          {verdict.get('state')}")
    print(f"  merge          {verdict.get('merge_decision')}")
    print(f"  trust score    {verdict.get('trust_score')}/100")
    if result.get("recruited"):
        print(f"  recruited      {', '.join(result['recruited'])}")
    for blocker in verdict.get("blockers", []):
        print(f"  BLOCKER        {blocker}")
    for condition in verdict.get("conditions", []):
        print(f"  condition      {condition}")
    ledger = verdict.get("ledger", [])
    if ledger:
        print("\n  ledger:")
        for row in ledger:
            print(f"    {row.get('requirement_id', '—'):<6} {row.get('decision', ''):<10} {row.get('requirement', '')}")


def _cmd_ghost(args: argparse.Namespace) -> int:
    ticket = _read_source(args.ticket)
    diff = _resolve_diff(args)
    if not diff.strip():
        return _empty_diff_exit(args)
    docket = build_adhoc_docket(ticket, diff)
    missing = ghost_check_docket(docket)
    if args.json:
        print(json.dumps({"missing": missing, "count": len(missing), "conforms": not missing}, indent=2))
    elif getattr(args, "quiet", False):
        pass
    elif missing:
        print(f"{len(missing)} requested item(s) missing from the diff:")
        for item in missing:
            print(f"  [{item.get('severity')}] {item.get('requirement_id')} · {item.get('requirement')}")
    else:
        print("No omissions — every requirement has implementing evidence.")
    return EXIT_BLOCK if missing else EXIT_OK


def _cmd_drift(args: argparse.Namespace) -> int:
    ticket = _read_source(args.ticket)
    diff = _resolve_diff(args)
    if not diff.strip():
        return _empty_diff_exit(args)
    docket = build_adhoc_docket(ticket, diff)
    drifts = drift_check_docket(docket)
    if args.json:
        print(json.dumps({"drifts": drifts, "count": len(drifts), "in_scope": not drifts}, indent=2))
    elif getattr(args, "quiet", False):
        pass
    elif drifts:
        print(f"{len(drifts)} unauthorized change(s):")
        for item in drifts:
            print(f"  {item.get('file_ref')} · {item.get('summary')}")
    else:
        print("No scope drift — every change traces back to a requirement.")
    return EXIT_BLOCK if drifts else EXIT_OK


def _cmd_init(args: argparse.Namespace) -> int:
    """Print (or write) the MCP wiring block for a coding agent."""
    groq_key = args.groq_key or args.key  # --key is the legacy alias for --groq-key
    try:
        block = render_agent_config(
            args.agent,
            api_key=groq_key,
            cerebras_key=args.cerebras_key,
            gemini_key=args.gemini_key,
            providers=args.providers,
            groq_model=args.groq_model,
            cerebras_model=args.cerebras_model,
            gemini_model=args.gemini_model,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BLOCK

    if args.write:
        writable = writable_config_path(args.agent)
        if writable is None:
            # App-UI-configured agent (Claude/Cursor) — no file to write.
            print(f"# {args.agent}: paste this into {config_target_path(args.agent)}", file=sys.stderr)
            print(block)
            return EXIT_OK
        path = os.path.expanduser(writable)
        if os.path.exists(path):
            # Never clobber an existing config — it holds more than our server.
            print(f"# {path} exists — merge this block in:", file=sys.stderr)
            print(block)
            return EXIT_OK
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(block + "\n")
        print(f"wrote {args.agent} config to {path}", file=sys.stderr)
        return EXIT_OK

    print(block)
    print(
        f"# paste into {config_target_path(args.agent)} — Tribunal is BYO-key: "
        "any free-tier key works (Groq, Cerebras, or Gemini). Run `tribunal doctor` to verify.",
        file=sys.stderr,
    )
    return EXIT_OK


def _cmd_doctor(args: argparse.Namespace) -> int:
    """Check each provider in the chain: key present? does a live call answer?

    Never prints any part of a key. Exit 0 when at least one provider is
    usable (live PASS, or key present in ``--offline`` mode), else 1.
    """
    rows: list[dict] = []
    for provider in tribunal_llm.chain():
        env_var = tribunal_llm.key_env_var(provider)
        key_present = bool(tribunal_llm.resolve_key(provider))
        try:
            model = tribunal_llm.resolve_model(provider)
        except ValueError:
            model = None
        row: dict = {
            "provider": provider,
            "env_var": env_var or None,
            "key_present": key_present,
            "model": model,
        }
        if not key_present:
            row["status"] = "MISSING"
            row["detail"] = f"set {env_var}" if env_var else "unknown provider"
        elif args.offline:
            row["status"] = "SET"
            row["detail"] = "key present (offline check — no live call made)"
        else:
            ok, detail = tribunal_llm.ping(provider)
            row["status"] = "PASS" if ok else "FAIL"
            row["detail"] = detail
        rows.append(row)

    if args.offline:
        healthy = any(row["status"] == "SET" for row in rows)
    else:
        healthy = any(row["status"] == "PASS" for row in rows)

    if args.json:
        print(json.dumps({"offline": args.offline, "ok": healthy, "providers": rows}, indent=2))
        return EXIT_OK if healthy else EXIT_BLOCK

    print("tribunal doctor — BYO-key health check (keys are never printed)")
    for row in rows:
        key_state = "KEY SET" if row["key_present"] else "KEY MISSING"
        parts = [f"{row['provider']:<9}", f"{key_state:<12}"]
        if row["status"] in ("PASS", "FAIL"):
            parts.append(f"{row['status']:<5}")
            parts.append(f"model={row['model']}")
        elif row["status"] == "SET":
            parts.append(f"model={row['model']}")
        if row.get("detail"):
            parts.append(f"— {row['detail']}")
        print("  " + " ".join(parts))
    if healthy:
        print("result: OK — at least one provider is ready.")
    else:
        print(
            "result: NOT READY — no working provider. Bring any free-tier key "
            "(GROQ_API_KEY, CEREBRAS_API_KEY, or GEMINI_API_KEY)."
        )
    return EXIT_OK if healthy else EXIT_BLOCK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tribunal",
        description="Intent-conformance review: did the diff build what the ticket asked for?",
        epilog=(
            "Exit codes: 0 = clear to merge, 1 = blocked / findings / error.\n"
            "stdout = data (use --json for machine output), stderr = logs/errors.\n"
            "Built to be called by AI agents in a write -> verify -> fix loop, e.g.\n"
            "  tribunal verify --ticket ticket.md --git || <agent fixes and retries>"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_io(p: argparse.ArgumentParser) -> None:
        p.add_argument("--ticket", required=True, help="Ticket text file, or - for stdin")
        src = p.add_mutually_exclusive_group(required=True)
        src.add_argument("--diff", help="Unified diff file, or - for stdin")
        src.add_argument(
            "--git",
            nargs="?",
            const="HEAD",
            default=None,
            metavar="REF",
            help="Run `git diff REF` for the diff (default HEAD = all uncommitted changes)",
        )

    quiet_help = "Suppress human output; rely on the exit code (for agent loops)"

    p_verify = sub.add_parser("verify", help="Full tribunal — verdict + trust score + ledger")
    add_io(p_verify)
    p_verify.add_argument("--domains", help="Comma-separated domain hints, e.g. auth,payments")
    p_verify.add_argument("--title", help="Optional docket title")
    p_verify.add_argument("--json", action="store_true", help="Emit the raw result as JSON")
    p_verify.add_argument("--quiet", action="store_true", help=quiet_help)
    p_verify.set_defaults(func=_cmd_verify)

    p_ghost = sub.add_parser("ghost", help="Fast omission pre-check")
    add_io(p_ghost)
    p_ghost.add_argument("--json", action="store_true", help="Emit the raw result as JSON")
    p_ghost.add_argument("--quiet", action="store_true", help=quiet_help)
    p_ghost.set_defaults(func=_cmd_ghost)

    p_drift = sub.add_parser("drift", help="Fast scope-drift pre-check")
    add_io(p_drift)
    p_drift.add_argument("--json", action="store_true", help="Emit the raw result as JSON")
    p_drift.add_argument("--quiet", action="store_true", help=quiet_help)
    p_drift.set_defaults(func=_cmd_drift)

    p_init = sub.add_parser(
        "init",
        help="Print the MCP wiring block for a coding agent",
        description=(
            "Emit the ready-to-paste Tribunal MCP server block for an agent. "
            "Tribunal is BYO-key: bring any free-tier key — Groq, Cerebras, or "
            "Gemini — via --groq-key/--cerebras-key/--gemini-key, and optionally "
            "set the fallback order with --providers."
        ),
    )
    p_init.add_argument("agent", choices=SUPPORTED_AGENTS, help="Target agent")
    p_init.add_argument(
        "--key",
        help="Alias for --groq-key (kept for backwards compatibility)",
    )
    p_init.add_argument("--groq-key", help="Bake in a real GROQ_API_KEY instead of the placeholder")
    p_init.add_argument("--cerebras-key", help="Bake in a real CEREBRAS_API_KEY")
    p_init.add_argument("--gemini-key", help="Bake in a real GEMINI_API_KEY")
    p_init.add_argument("--groq-model", help="Override the Groq model (GROQ_MODEL)")
    p_init.add_argument("--cerebras-model", help="Override the Cerebras model (CEREBRAS_MODEL)")
    p_init.add_argument("--gemini-model", help="Override the Gemini model (GEMINI_MODEL)")
    p_init.add_argument(
        "--providers",
        help='Provider fallback chain (TRIBUNAL_LLM_PROVIDERS), e.g. "groq,cerebras,gemini"',
    )
    p_init.add_argument(
        "--write",
        action="store_true",
        help="Write to the agent's config path (never clobbers an existing file)",
    )
    p_init.set_defaults(func=_cmd_init)

    p_doctor = sub.add_parser(
        "doctor",
        help="Check that your BYO provider keys work (Groq/Cerebras/Gemini)",
        description=(
            "For each provider in the chain (TRIBUNAL_LLM_PROVIDERS, default "
            "groq,cerebras,gemini): report whether its key is set and, unless "
            "--offline, fire a minimal 1-token live completion to prove it works. "
            "Keys are never printed. Exit 0 when at least one provider is usable."
        ),
    )
    p_doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_doctor.add_argument(
        "--offline",
        action="store_true",
        help="Only check key presence; make no network calls",
    )
    p_doctor.set_defaults(func=_cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Render unicode separators (·, —) correctly on Windows consoles (cp1252).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
            pass
    # Pick up a .env from the CWD (the repo being verified) so `tribunal` works
    # without exporting keys by hand; real env vars still take precedence, and
    # we never walk up from this module's own source tree.
    try:
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv(usecwd=True))
    except Exception:  # pragma: no cover - dotenv is a hard dep, but stay safe
        pass
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BLOCK
    except Exception as exc:  # pragma: no cover - defensive
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BLOCK


if __name__ == "__main__":
    sys.exit(main())
