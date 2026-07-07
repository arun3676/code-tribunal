"""Wiring config for coding agents — single source of truth for `tribunal init`.

Code Tribunal ships an MCP server (`tribunal-mcp`); every supported agent is an
MCP *client*, so "integrating" Tribunal is mostly dropping one server block into
that agent's config. This module renders those blocks so the CLI, the committed
samples under ``integrations/``, and the docs never drift apart.

Every block invokes the same clone-free entry point used everywhere else::

    uvx --from code-tribunal tribunal-mcp

with ``GROQ_API_KEY`` supplied via the agent's ``env``. The placeholder is left
in by default; pass ``api_key=`` (CLI: ``--key`` / ``--groq-key``) to bake a
real key in. Tribunal is BYO-key across three free-tier providers — Groq,
Cerebras, Gemini — so the renderer also accepts per-provider keys, per-provider
model overrides, and a provider-chain string (``TRIBUNAL_LLM_PROVIDERS``).
The default output (no extra arguments) is intentionally byte-identical to the
Groq-only block so the committed samples never churn.
"""

from __future__ import annotations

import json

SUPPORTED_AGENTS = ["openclaw", "hermes", "claude", "codex", "cursor"]

KEY_PLACEHOLDER = "<your GROQ_API_KEY>"

# Providers the tribunal reasoning chain understands (see tribunal/llm.py).
SUPPORTED_PROVIDERS = ("groq", "cerebras", "gemini")

_PROVIDER_KEY_ENV = {
    "groq": "GROQ_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def key_placeholder(provider: str) -> str:
    """Placeholder text for a provider key, e.g. ``<your CEREBRAS_API_KEY>``."""
    return f"<your {_PROVIDER_KEY_ENV[provider]}>"

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


def _build_env(
    api_key: str | None,
    cerebras_key: str | None,
    gemini_key: str | None,
    providers: str | None,
    groq_model: str | None,
    cerebras_model: str | None,
    gemini_model: str | None,
) -> dict[str, str]:
    """Assemble the MCP ``env`` block in a stable, documented order.

    Order: GROQ_API_KEY (always) → CEREBRAS_API_KEY → GEMINI_API_KEY →
    TRIBUNAL_LLM_PROVIDERS → GROQ_MODEL → CEREBRAS_MODEL → GEMINI_MODEL,
    including only the entries actually requested. With no extras this is
    exactly ``{"GROQ_API_KEY": ...}`` — byte-identical legacy output.
    """
    chain: list[str] | None = None
    if providers is not None:
        chain = [p.strip().lower() for p in providers.split(",") if p.strip()]
        unknown = [p for p in chain if p not in SUPPORTED_PROVIDERS]
        if unknown:
            raise ValueError(
                f"unknown provider(s): {', '.join(unknown)}. "
                f"Supported: {', '.join(SUPPORTED_PROVIDERS)}"
            )
        if not chain:
            raise ValueError(
                f"providers must name at least one of: {', '.join(SUPPORTED_PROVIDERS)}"
            )

    env: dict[str, str] = {"GROQ_API_KEY": api_key or KEY_PLACEHOLDER}
    if cerebras_key or (chain and "cerebras" in chain):
        env["CEREBRAS_API_KEY"] = cerebras_key or key_placeholder("cerebras")
    if gemini_key or (chain and "gemini" in chain):
        env["GEMINI_API_KEY"] = gemini_key or key_placeholder("gemini")
    if chain:
        env["TRIBUNAL_LLM_PROVIDERS"] = ",".join(chain)
    if groq_model:
        env["GROQ_MODEL"] = groq_model
    if cerebras_model:
        env["CEREBRAS_MODEL"] = cerebras_model
    if gemini_model:
        env["GEMINI_MODEL"] = gemini_model
    return env


def _server_dict(env: dict[str, str]) -> dict:
    """The stdio MCP server entry shared by the JSON-shaped agents."""
    return {
        "command": _COMMAND,
        "args": list(_ARGS),
        "env": dict(env),
    }


def _render_json_nested(outer_key: str, env: dict[str, str]) -> str:
    """Render a ``{<outer_key>: {servers...: {tribunal: {...}}}}`` JSON block."""
    if outer_key == "mcp":  # OpenClaw nests under mcp.servers
        body = {"mcp": {"servers": {"tribunal": _server_dict(env)}}}
    else:  # Claude / Cursor use a flat mcpServers map
        body = {"mcpServers": {"tribunal": _server_dict(env)}}
    return json.dumps(body, indent=2)


def _render_codex_toml(env: dict[str, str]) -> str:
    args = ", ".join(json.dumps(a) for a in _ARGS)
    pairs = ", ".join(f"{name} = {json.dumps(value)}" for name, value in env.items())
    return (
        "[mcp_servers.tribunal]\n"
        f'command = "{_COMMAND}"\n'
        f"args = [{args}]\n"
        f"env = {{ {pairs} }}\n"
    )


def _render_hermes_yaml(env: dict[str, str]) -> str:
    args = ", ".join(json.dumps(a) for a in _ARGS)
    include = ", ".join(_TOOLS)
    env_lines = "".join(f'      {name}: "{value}"\n' for name, value in env.items())
    return (
        "mcp_servers:\n"
        "  tribunal:\n"
        f'    command: "{_COMMAND}"\n'
        f"    args: [{args}]\n"
        "    env:\n"
        f"{env_lines}"
        "    tools:\n"
        f"      include: [{include}]\n"
        "    enabled: true\n"
    )


def render_agent_config(
    agent: str,
    api_key: str | None = None,
    *,
    cerebras_key: str | None = None,
    gemini_key: str | None = None,
    providers: str | None = None,
    groq_model: str | None = None,
    cerebras_model: str | None = None,
    gemini_model: str | None = None,
) -> str:
    """Return the ready-to-paste config block for ``agent``.

    Output is deterministic and the canonical source for the committed
    ``integrations/`` samples (a test asserts they match byte-for-byte);
    calling with only ``agent`` (and optionally ``api_key``) renders the
    classic Groq-only block, unchanged.

    Args:
        agent: One of ``SUPPORTED_AGENTS``.
        api_key: Real Groq key to bake in instead of the placeholder.
        cerebras_key / gemini_key: Real keys for the other free providers.
        providers: Comma-separated chain for ``TRIBUNAL_LLM_PROVIDERS``
            (e.g. ``"groq,cerebras,gemini"``). Providers named here without a
            key get a ``<your ..._API_KEY>`` placeholder.
        groq_model / cerebras_model / gemini_model: Optional model overrides
            (``GROQ_MODEL`` / ``CEREBRAS_MODEL`` / ``GEMINI_MODEL``).
    """
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(
            f"unknown agent '{agent}'. Supported: {', '.join(SUPPORTED_AGENTS)}"
        )
    env = _build_env(
        api_key, cerebras_key, gemini_key, providers,
        groq_model, cerebras_model, gemini_model,
    )
    if agent == "openclaw":
        return _render_json_nested("mcp", env)
    if agent in ("claude", "cursor"):
        return _render_json_nested("mcpServers", env)
    if agent == "codex":
        return _render_codex_toml(env)
    if agent == "hermes":
        return _render_hermes_yaml(env)
    raise AssertionError(f"unhandled agent {agent}")  # pragma: no cover


__all__ = [
    "SUPPORTED_AGENTS",
    "SUPPORTED_PROVIDERS",
    "KEY_PLACEHOLDER",
    "key_placeholder",
    "render_agent_config",
    "config_target_path",
    "writable_config_path",
]
