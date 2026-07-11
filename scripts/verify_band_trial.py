#!/usr/bin/env python3
"""Smoke-test Band Agent API integration before deploy.

Usage (from repo root):
    python scripts/verify_band_trial.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in __import__("os").environ:
            __import__("os").environ[key] = value


async def main() -> int:
    load_env(ROOT / ".env")
    load_env(ROOT / "apps" / "api" / ".env")

    from code_council.tribunal.band_adapter import AGENT_HANDLES, BandAdapter, BandError

    band = BandAdapter()
    if not band.enabled:
        print("ERROR: Set BAND_ENABLED=true and BAND_API_KEY in .env")
        return 1

    try:
        me = await band.verify_me("CLERK")
    except Exception as exc:
        print(f"ERROR: GET /agent/me failed: {exc}")
        return 1

    handle = me.get("handle") or me.get("agent", {}).get("handle") or AGENT_HANDLES["CLERK"]
    if not handle.startswith("@"):
        handle = f"@{handle}"
    print(f"BAND OK: clerk = {handle}")

    try:
        chat_id = await band.create_room("Tribunal smoke test")
    except BandError as exc:
        print(f"ERROR: create_room failed: {exc}")
        return 1
    if not chat_id:
        print("ERROR: create_room returned no chat id")
        return 1
    print(f"CHAT OK: {chat_id}")

    try:
        await band.add_participant(chat_id, "ADVOCATE")
    except BandError as exc:
        print(f"ERROR: add_participant failed: {exc}")
        return 1
    print("PARTICIPANT OK: ADVOCATE")

    advocate_handle = AGENT_HANDLES["ADVOCATE"]
    try:
        await band.send_message(
            chat_id,
            "CLERK",
            "Please extract requirements from this docket.",
            targets=["ADVOCATE"],
        )
    except BandError as exc:
        print(f"ERROR: send_message failed: {exc}")
        return 1
    print(f"MESSAGE OK: @{advocate_handle}")

    try:
        await band.post_event(
            chat_id,
            "GHOST",
            "omission",
            {"requirement_id": "R3", "severity": "critical"},
            text="GHOST found R3 unmet: rate limiting is missing.",
        )
    except BandError as exc:
        print(f"ERROR: post_event failed: {exc}")
        return 1
    print("EVENT OK: tool_result")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
