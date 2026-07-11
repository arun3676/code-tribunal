"""The runtime __version__ must match the packaging metadata."""

from __future__ import annotations

import tomllib
from pathlib import Path

import code_council


def test_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as fh:
        declared = tomllib.load(fh)["project"]["version"]
    assert code_council.__version__ == declared
