# Code Tribunal — agent integrations

Code Tribunal is an **intent-conformance gate**: it answers "did this diff build what the
ticket actually asked for?" It ships as an MCP server (`tribunal-mcp`), and every agent here
is a first-class **MCP client** — so wiring Tribunal in is mostly dropping one server block
into the agent's config.

## The three tools your agent gets

| Tool | Answers | Cost |
|------|---------|------|
| `verify_intent_conformance` | Full court — trust score, merge decision, blockers, traceability ledger | Full |
| `ghost_check` | "Did I miss any requested requirements?" | Fast, deterministic |
| `drift_check` | "Did I change something no requirement authorized?" | Fast, deterministic |

Treat `merge_decision == "BLOCK"` as the universal *loop-and-fix* signal.

## Generate the config

The blocks under each folder are the verbatim output of the CLI emitter (a test keeps them in
sync), so you can also generate them on the fly:

```bash
tribunal init openclaw      # JSON for ~/.openclaw/openclaw.json
tribunal init hermes        # YAML for ~/.hermes/config.yaml
tribunal init claude        # mcpServers JSON (Claude Code / Cursor)
tribunal init codex         # ~/.codex/config.toml
tribunal init --help        # all supported agents
```

## Per-agent guides

- [`openclaw/`](openclaw/) — self-hosted gateway, MCP via `openclaw mcp add`.
- [`hermes/`](hermes/) — autonomous agent (Nous Research), MCP + an [Open Skill](hermes/skill/SKILL.md).

For the full design rationale (why MCP is the spine, and what a deeper native integration
would look like), see `docs/explainers/agent-integrations.html`.
