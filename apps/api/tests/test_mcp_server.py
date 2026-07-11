"""MCP server e2e — drives the real protocol over the SDK's in-memory transport.

`create_connected_server_and_client_session` performs the actual MCP
initialize handshake against the same low-level server that `tribunal-mcp`
serves over stdio, so tool discovery and calls here exercise the full protocol
path without a subprocess (offline / deterministic).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.shared.memory import create_connected_server_and_client_session

from code_council import mcp_server
from code_council.tribunal.fixtures import get_fixture

EXPECTED_TOOLS = {"verify_intent_conformance", "ghost_check", "drift_check"}


def _fixture_case(fixture_id: str) -> tuple[str, str]:
    docket = get_fixture(fixture_id)
    return docket.intent_sources[0].text, docket.diff


def _result_payload(result: Any) -> dict:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        # FastMCP wraps plain-dict returns under a "result" key on some SDK
        # versions; unwrap when present.
        return structured.get("result", structured)
    text = next(block.text for block in result.content if hasattr(block, "text"))
    return json.loads(text)


async def _list_tool_names() -> set[str]:
    async with create_connected_server_and_client_session(mcp_server.mcp._mcp_server) as session:
        listed = await session.list_tools()
        return {tool.name for tool in listed.tools}


async def _call_tool(name: str, arguments: dict) -> dict:
    async with create_connected_server_and_client_session(mcp_server.mcp._mcp_server) as session:
        result = await session.call_tool(name, arguments)
        assert not result.isError, f"tool {name} errored: {result.content}"
        return _result_payload(result)


def test_lists_exactly_the_three_tribunal_tools():
    assert asyncio.run(_list_tool_names()) == EXPECTED_TOOLS


def test_verify_blocks_nonconforming_auth_diff():
    ticket, diff = _fixture_case("auth-login-001")
    payload = asyncio.run(
        _call_tool(
            "verify_intent_conformance",
            {"ticket_description": ticket, "git_diff": diff},
        )
    )
    verdict = payload["verdict"]
    assert verdict["merge_decision"] == "BLOCK"
    assert 0 <= verdict["trust_score"] <= 100
    assert payload["headline"]


def test_verify_approves_conforming_health_diff():
    ticket, diff = _fixture_case("health-check-002")
    payload = asyncio.run(
        _call_tool(
            "verify_intent_conformance",
            {"ticket_description": ticket, "git_diff": diff},
        )
    )
    assert payload["verdict"]["merge_decision"] in ("APPROVE", "APPROVE_WITH_CONDITIONS")


def test_ghost_check_reports_missing_requirements():
    ticket, diff = _fixture_case("auth-login-001")
    payload = asyncio.run(
        _call_tool("ghost_check", {"ticket_description": ticket, "git_diff": diff})
    )
    # The auth fixture omits rate limiting — ghost must flag it.
    assert payload["count"] >= 1
    assert payload["conforms"] is False
    assert payload["count"] == len(payload["missing"])


def test_drift_check_returns_scope_report():
    ticket, diff = _fixture_case("health-check-002")
    payload = asyncio.run(
        _call_tool("drift_check", {"ticket_description": ticket, "git_diff": diff})
    )
    assert set(payload) == {"drifts", "count", "in_scope"}
    assert payload["count"] == len(payload["drifts"])
