"""Command-line interface for Code Tribunal.

Wraps the same headless engine the MCP server and web API use, for CI gating and
local checks. The ``verify`` command exits non-zero on a BLOCK verdict so it can
be dropped straight into a pipeline:

    tribunal verify --ticket ticket.md --diff pr.diff || exit 1

Subcommands:
    verify   full court — trust score, merge decision, blockers, ledger
    ghost    fast omission pre-check (requested-but-missing requirements)
    drift    fast scope-drift pre-check (changes no requirement authorized)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

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


def _cmd_verify(args: argparse.Namespace) -> int:
    ticket = _read_source(args.ticket)
    diff = _read_source(args.diff)
    docket = build_adhoc_docket(ticket, diff, _split_domains(args.domains), args.title)
    result = asyncio.run(run_trial_collect(docket))
    result["headline"] = summarize_verdict(result.get("verdict"))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
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
    docket = build_adhoc_docket(_read_source(args.ticket), _read_source(args.diff))
    missing = ghost_check_docket(docket)
    if args.json:
        print(json.dumps({"missing": missing, "count": len(missing), "conforms": not missing}, indent=2))
    elif missing:
        print(f"{len(missing)} requested item(s) missing from the diff:")
        for item in missing:
            print(f"  [{item.get('severity')}] {item.get('requirement_id')} · {item.get('requirement')}")
    else:
        print("No omissions — every requirement has implementing evidence.")
    return EXIT_BLOCK if missing else EXIT_OK


def _cmd_drift(args: argparse.Namespace) -> int:
    docket = build_adhoc_docket(_read_source(args.ticket), _read_source(args.diff))
    drifts = drift_check_docket(docket)
    if args.json:
        print(json.dumps({"drifts": drifts, "count": len(drifts), "in_scope": not drifts}, indent=2))
    elif drifts:
        print(f"{len(drifts)} unauthorized change(s):")
        for item in drifts:
            print(f"  {item.get('file_ref')} · {item.get('summary')}")
    else:
        print("No scope drift — every change traces back to a requirement.")
    return EXIT_BLOCK if drifts else EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tribunal",
        description="Intent-conformance review: did the diff build what the ticket asked for?",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_io(p: argparse.ArgumentParser) -> None:
        p.add_argument("--ticket", required=True, help="Ticket text file, or - for stdin")
        p.add_argument("--diff", required=True, help="Unified diff file, or - for stdin")

    p_verify = sub.add_parser("verify", help="Full tribunal — verdict + trust score + ledger")
    add_io(p_verify)
    p_verify.add_argument("--domains", help="Comma-separated domain hints, e.g. auth,payments")
    p_verify.add_argument("--title", help="Optional docket title")
    p_verify.add_argument("--json", action="store_true", help="Emit the raw result as JSON")
    p_verify.set_defaults(func=_cmd_verify)

    p_ghost = sub.add_parser("ghost", help="Fast omission pre-check")
    add_io(p_ghost)
    p_ghost.add_argument("--json", action="store_true")
    p_ghost.set_defaults(func=_cmd_ghost)

    p_drift = sub.add_parser("drift", help="Fast scope-drift pre-check")
    add_io(p_drift)
    p_drift.add_argument("--json", action="store_true")
    p_drift.set_defaults(func=_cmd_drift)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Render unicode separators (·, —) correctly on Windows consoles (cp1252).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
            pass
    # Pick up a local .env (gitignored) so `tribunal` works without exporting
    # keys by hand; real env vars and MCP `env` blocks still take precedence.
    try:
        from dotenv import load_dotenv

        load_dotenv()
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
