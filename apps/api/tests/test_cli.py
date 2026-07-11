"""CLI exit-code semantics (offline / deterministic)."""

from __future__ import annotations

from code_council import cli
from code_council.tribunal.fixtures import get_fixture


def _write_case(tmp_path, fixture_id):
    docket = get_fixture(fixture_id)
    ticket = tmp_path / "ticket.md"
    diff = tmp_path / "pr.diff"
    ticket.write_text(docket.intent_sources[0].text, encoding="utf-8")
    diff.write_text(docket.diff, encoding="utf-8")
    return str(ticket), str(diff)


def test_verify_blocks_with_exit_1(tmp_path, capsys):
    ticket, diff = _write_case(tmp_path, "auth-login-001")
    code = cli.main(["verify", "--ticket", ticket, "--diff", diff])
    assert code == 1
    assert "BLOCK" in capsys.readouterr().out


def test_verify_approves_with_exit_0(tmp_path, capsys):
    ticket, diff = _write_case(tmp_path, "health-check-002")
    code = cli.main(["verify", "--ticket", ticket, "--diff", diff])
    assert code == 0
    assert "APPROVE" in capsys.readouterr().out


def test_verify_json_flag(tmp_path, capsys):
    ticket, diff = _write_case(tmp_path, "health-check-002")
    code = cli.main(["verify", "--ticket", ticket, "--diff", diff, "--json"])
    assert code == 0
    out = capsys.readouterr().out
    assert '"verdict"' in out and '"merge_decision"' in out


def test_ghost_flags_missing_requirement(tmp_path):
    ticket, diff = _write_case(tmp_path, "auth-login-001")
    # auth fixture omits rate limiting -> ghost should report a miss and exit 1.
    assert cli.main(["ghost", "--ticket", ticket, "--diff", diff]) == 1
