"""Set Railway Band variables from local .env (no values printed)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = [
    "BAND_ENABLED",
    "BAND_STRICT",
    "BAND_API_KEY",
    "BAND_BASE_URL",
    "BAND_CLERK_ID",
    "BAND_ADVOCATE_ID",
    "BAND_SURVEYOR_ID",
    "BAND_GHOST_ID",
    "BAND_DRIFT_ID",
    "BAND_WARDEN_ID",
    "BAND_ARBITER_ID",
]


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
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    load_env(ROOT / ".env")
    load_env(ROOT / "apps" / "api" / ".env")
    os.environ.setdefault("BAND_ENABLED", "true")
    os.environ.setdefault("BAND_STRICT", "true")
    pairs = [f"{k}={os.environ[k]}" for k in KEYS if os.environ.get(k)]
    if not pairs:
        print("ERROR: no Band keys found in .env")
        return 1
    subprocess.run(
        "railway variables set " + " ".join(f'"{p}"' for p in pairs),
        cwd=ROOT / "apps" / "api",
        check=True,
        shell=True,
    )
    print(f"Set {len(pairs)} Railway variables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
