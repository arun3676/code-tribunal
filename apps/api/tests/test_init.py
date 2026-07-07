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


# --- Multi-provider BYO-key rendering ----------------------------------------

_EXPECTED_FULL_ENV = {
    "GROQ_API_KEY": "gk-1",
    "CEREBRAS_API_KEY": "ck-2",
    "GEMINI_API_KEY": "mk-3",
    "TRIBUNAL_LLM_PROVIDERS": "groq,cerebras,gemini",
    "GROQ_MODEL": "groq-model-x",
    "CEREBRAS_MODEL": "cerebras-model-y",
    "GEMINI_MODEL": "gemini-model-z",
}

_FULL_KWARGS = dict(
    api_key="gk-1",
    cerebras_key="ck-2",
    gemini_key="mk-3",
    providers="groq,cerebras,gemini",
    groq_model="groq-model-x",
    cerebras_model="cerebras-model-y",
    gemini_model="gemini-model-z",
)


@pytest.mark.parametrize("agent", SUPPORTED_AGENTS)
def test_default_output_has_no_multiprovider_entries(agent):
    """No new args -> classic Groq-only block (drift-guard safety net)."""
    out = render_agent_config(agent)
    for var in ("CEREBRAS_API_KEY", "GEMINI_API_KEY", "TRIBUNAL_LLM_PROVIDERS",
                "GROQ_MODEL", "CEREBRAS_MODEL", "GEMINI_MODEL"):
        assert var not in out


def test_multikey_json_env_order_openclaw():
    out = render_agent_config("openclaw", **_FULL_KWARGS)
    env = json.loads(out)["mcp"]["servers"]["tribunal"]["env"]
    assert env == _EXPECTED_FULL_ENV
    assert list(env) == list(_EXPECTED_FULL_ENV)  # stable documented order


@pytest.mark.parametrize("agent", ["claude", "cursor"])
def test_multikey_json_env_claude_cursor(agent):
    out = render_agent_config(agent, **_FULL_KWARGS)
    env = json.loads(out)["mcpServers"]["tribunal"]["env"]
    assert env == _EXPECTED_FULL_ENV


def test_multikey_toml_env_codex():
    out = render_agent_config("codex", **_FULL_KWARGS)
    env = tomllib.loads(out)["mcp_servers"]["tribunal"]["env"]
    assert env == _EXPECTED_FULL_ENV


def test_multikey_yaml_env_hermes():
    out = render_agent_config("hermes", **_FULL_KWARGS)
    for name, value in _EXPECTED_FULL_ENV.items():
        assert f'      {name}: "{value}"' in out
    # Stable order: entries appear in the documented sequence.
    positions = [out.index(name) for name in _EXPECTED_FULL_ENV]
    assert positions == sorted(positions)


def test_providers_without_keys_get_placeholders():
    out = render_agent_config("openclaw", providers="groq,cerebras,gemini")
    env = json.loads(out)["mcp"]["servers"]["tribunal"]["env"]
    assert env["GROQ_API_KEY"] == "<your GROQ_API_KEY>"
    assert env["CEREBRAS_API_KEY"] == "<your CEREBRAS_API_KEY>"
    assert env["GEMINI_API_KEY"] == "<your GEMINI_API_KEY>"
    assert env["TRIBUNAL_LLM_PROVIDERS"] == "groq,cerebras,gemini"


def test_model_override_only():
    out = render_agent_config("openclaw", cerebras_model="new-model")
    env = json.loads(out)["mcp"]["servers"]["tribunal"]["env"]
    assert env == {"GROQ_API_KEY": KEY_PLACEHOLDER, "CEREBRAS_MODEL": "new-model"}


def test_invalid_providers_rejected():
    with pytest.raises(ValueError, match="unknown provider"):
        render_agent_config("openclaw", providers="groq,bogus")


def test_cli_invalid_providers_exit_1(capsys):
    assert cli.main(["init", "openclaw", "--providers", "groq,bogus"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unknown provider" in captured.err


def test_cli_key_alias_equals_groq_key(capsys):
    assert cli.main(["init", "openclaw", "--key", "sk-alias"]) == 0
    via_alias = capsys.readouterr().out
    assert cli.main(["init", "openclaw", "--groq-key", "sk-alias"]) == 0
    via_flag = capsys.readouterr().out
    assert via_alias == via_flag
    assert "sk-alias" in via_alias


def test_cli_multikey_flags(capsys):
    assert cli.main([
        "init", "codex",
        "--groq-key", "gk-1",
        "--cerebras-key", "ck-2",
        "--gemini-key", "mk-3",
        "--providers", "groq,cerebras,gemini",
        "--groq-model", "groq-model-x",
        "--cerebras-model", "cerebras-model-y",
        "--gemini-model", "gemini-model-z",
    ]) == 0
    env = tomllib.loads(capsys.readouterr().out)["mcp_servers"]["tribunal"]["env"]
    assert env == _EXPECTED_FULL_ENV


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
