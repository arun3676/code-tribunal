"""`tribunal init` emitter + the committed-sample drift guard (offline)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from code_council import cli
from code_council.agent_config import (
    SUPPORTED_AGENTS,
    KEY_PLACEHOLDER,
    render_agent_config,
)
from code_council.tribunal.fixtures import get_fixture

# Repo root: .../apps/api/tests/test_init.py -> parents[3] == code-tribunal/
_INTEGRATIONS = Path(__file__).resolve().parents[3] / "integrations"


def _norm(text: str) -> str:
    """Compare ignoring trailing newlines / CRLF so the guard is OS-agnostic."""
    return text.replace("\r\n", "\n").strip()


def test_init_openclaw_is_valid_json(capsys):
    assert cli.main(["init", "openclaw"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["mcp"]["servers"]["tribunal"]["command"] == "uvx"


@pytest.mark.parametrize("agent", ["claude", "cursor"])
def test_init_claude_cursor_mcpservers_json(agent, capsys):
    assert cli.main(["init", agent]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["mcpServers"]["tribunal"]["args"] == ["--from", "code-tribunal", "tribunal-mcp"]


def test_init_codex_is_valid_toml(capsys):
    assert cli.main(["init", "codex"]) == 0
    data = tomllib.loads(capsys.readouterr().out)
    assert data["mcp_servers"]["tribunal"]["command"] == "uvx"


def test_init_hermes_has_tool_filter(capsys):
    assert cli.main(["init", "hermes"]) == 0
    out = capsys.readouterr().out
    assert "mcp_servers:" in out
    assert "tribunal:" in out
    assert "include: [verify_intent_conformance, ghost_check, drift_check]" in out


def test_init_unknown_agent_exits_1(capsys):
    # argparse rejects an out-of-choice agent before our handler runs.
    with pytest.raises(SystemExit) as exc:
        cli.main(["init", "bogus"])
    assert exc.value.code != 0


def test_init_key_substitution(capsys):
    assert cli.main(["init", "openclaw", "--key", "sk-test-123"]) == 0
    out = capsys.readouterr().out
    assert "sk-test-123" in out and KEY_PLACEHOLDER not in out


@pytest.mark.parametrize("agent", SUPPORTED_AGENTS)
def test_default_uses_placeholder(agent):
    assert KEY_PLACEHOLDER in render_agent_config(agent)


# --- Drift guard: committed samples must equal the emitter output -----------

@pytest.mark.parametrize(
    "agent,sample",
    [
        ("openclaw", _INTEGRATIONS / "openclaw" / "openclaw.json"),
        ("hermes", _INTEGRATIONS / "hermes" / "config.yaml"),
    ],
)
def test_committed_sample_matches_emitter(agent, sample):
    assert sample.exists(), f"missing committed sample: {sample}"
    assert _norm(sample.read_text(encoding="utf-8")) == _norm(render_agent_config(agent))


# --- Ergonomics: --quiet suppresses human output, keeps the exit code -------

def _write_case(tmp_path, fixture_id):
    docket = get_fixture(fixture_id)
    ticket = tmp_path / "ticket.md"
    diff = tmp_path / "pr.diff"
    ticket.write_text(docket.intent_sources[0].text, encoding="utf-8")
    diff.write_text(docket.diff, encoding="utf-8")
    return str(ticket), str(diff)


def test_verify_quiet_suppresses_stdout(tmp_path, capsys):
    ticket, diff = _write_case(tmp_path, "auth-login-001")
    code = cli.main(["verify", "--ticket", ticket, "--diff", diff, "--quiet"])
    assert code == 1  # still BLOCK
    assert capsys.readouterr().out == ""
