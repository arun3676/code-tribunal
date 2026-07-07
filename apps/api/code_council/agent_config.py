"""Wiring config for coding agents — single source of truth for `tribunal init`.

Code Tribunal ships an MCP server (`tribunal-mcp`); every supported agent is an
MCP *client*, so "integrating" Tribunal is mostly dropping one server block into
that agent's config. This module renders those blocks so the CLI, the committed
samples under ``integrations/``, and the docs never drift apart.

Every block invokes the same clone-free entry point used everywhere else::

    uvx --from code-tribunal tribunal-mcp

with ``GROQ_API_KEY`` supplied via the agent's ``env``. The placeholder is left
in by default; pass ``api_key=`` (CLI: ``--key``) to bake a real key in.
"""

from __future__ import annotations

import json

SUPPORTED_AGENTS = ["openclaw", "hermes", "claude", "codex", "cursor"]

KEY_PLACEHOLDER = "<your GROQ_API_KEY>"

# The command every agent runs to launch the Tribunal MCP server.
_COMMAND = "uvx"
_ARGS = ["--from", "code-tribunal", "tribunal-mcp"]

# The three tools the MCP server exposes (see mcp_server.py). The fast checks
# (ghost/drift) are deterministic; verify_intent_conformance convenes the court.
_TOOLS = ["verify_intent_conformance", "ghost_check", "drift_check"]

_TARGET_PATHS = {
    "openclaw": "~/.openclaw/openclaw.json",
    "hermes": "~/.hermes/config.yaml",
    "claude": "your Claude Code / claude_desktop_config.json (mcpServers)",
    "codex": "~/.codex/config.toml",
    "cursor": "your Cursor mcp.json (mcpServers)",
}

# Agents whose config is a known file `tribunal init --write` can create.
# Claude and Cursor are configured through their app UI (the targets above are
# guidance, not paths), so we only ever print their block — never write a file.
_WRITABLE_PATHS = {
    "openclaw": "~/.openclaw/openclaw.json",
    "hermes": "~/.hermes/config.yaml",
    "codex": "~/.codex/config.toml",
}


def config_target_path(agent: str) -> str:
    """Human-readable destination for an agent's config block."""
    return _TARGET_PATHS[agent]


def writable_config_path(agent: str) -> str | None:
    """Filesystem path ``--write`` may create, or ``None`` if the agent is
    configured through its app UI and has no file we should write."""
    return _WRITABLE_PATHS.get(agent)


def _server_dict(api_key: str) -> dict:
    """The stdio MCP server entry shared by the JSON-shaped agents."""
    return {
        "command": _COMMAND,
        "args": list(_ARGS),
        "env": {"GROQ_API_KEY": api_key},
    }


def _render_json_nested(outer_key: str, api_key: str) -> str:
    """Render a ``{<outer_key>: {servers...: {tribunal: {...}}}}`` JSON block."""
    if outer_key == "mcp":  # OpenClaw nests under mcp.servers
        body = {"mcp": {"servers": {"tribunal": _server_dict(api_key)}}}
    else:  # Claude / Cursor use a flat mcpServers map
        body = {"mcpServers": {"tribunal": _server_dict(api_key)}}
    return json.dumps(body, indent=2)


def _render_codex_toml(api_key: str) -> str:
    args = ", ".join(json.dumps(a) for a in _ARGS)
    return (
        "[mcp_servers.tribunal]\n"
        f'command = "{_COMMAND}"\n'
        f"args = [{args}]\n"
        f'env = {{ GROQ_API_KEY = "{api_key}" }}\n'
    )


def _render_hermes_yaml(api_key: str) -> str:
    args = ", ".join(json.dumps(a) for a in _ARGS)
    include = ", ".join(_TOOLS)
    return (
        "mcp_servers:\n"
        "  tribunal:\n"
        f'    command: "{_COMMAND}"\n'
        f"    args: [{args}]\n"
        "    env:\n"
        f'      GROQ_API_KEY: "{api_key}"\n'
        "    tools:\n"
        f"      include: [{include}]\n"
        "    enabled: true\n"
    )


def render_agent_config(agent: str, api_key: str | None = None) -> str:
    """Return the ready-to-paste config block for ``agent``.

    Output is deterministic and the canonical source for the committed
    ``integrations/`` samples (a test asserts they match byte-for-byte).
    """
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(
            f"unknown agent '{agent}'. Supported: {', '.join(SUPPORTED_AGENTS)}"
        )
    key = api_key or KEY_PLACEHOLDER
    if agent == "openclaw":
        return _render_json_nested("mcp", key)
    if agent in ("claude", "cursor"):
        return _render_json_nested("mcpServers", key)
    if agent == "codex":
        return _render_codex_toml(key)
    if agent == "hermes":
        return _render_hermes_yaml(key)
    raise AssertionError(f"unhandled agent {agent}")  # pragma: no cover


__all__ = [
    "SUPPORTED_AGENTS",
    "KEY_PLACEHOLDER",
    "render_agent_config",
    "config_target_path",
    "writable_config_path",
]
