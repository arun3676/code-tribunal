"""Report which env keys are set (never prints secret values)."""
from __future__ import annotations

from pathlib import Path

KEYS = [
    "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY",
    "MERCURY_API_KEY",
    "Kimi_API_KEY",
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
    "AIMLAPI_API_KEY",
    "FEATHERLESS_API_KEY",
    "ALLOWED_ORIGINS",
    "NEXT_PUBLIC_API_URL",
]


def load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> None:
    files = [
        ("root .env", Path(".env")),
        ("apps/api/.env", Path("apps/api/.env")),
        ("apps/web/.env.local", Path("apps/web/.env.local")),
    ]
    for label, path in files:
        env = load_env(path)
        print(f"=== {label} ({path}) ===")
        if not path.exists():
            print("  FILE NOT FOUND")
            continue
        for k in KEYS:
            v = env.get(k, "")
            if k == "BAND_ENABLED":
                print(f"  {k}: {v or '(unset)'}")
            elif v:
                print(f"  {k}: SET (len={len(v)})")
            else:
                print(f"  {k}: MISSING")
        extra = sorted(k for k in env if k not in KEYS and env.get(k))
        if extra:
            print(f"  other keys with values: {extra}")


if __name__ == "__main__":
    main()
