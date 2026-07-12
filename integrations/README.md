# Code Tribunal — agent integrations

Code Tribunal is an **intent-conformance gate**: it answers "did this diff build what the
ticket actually asked for?" It ships as an MCP server (`tribunal-mcp`), and every agent here
is a first-class **MCP client** — so wiring Tribunal in is mostly dropping one server block
into the agent's config.

> **Not on PyPI yet.** The sample blocks here (and the `tribunal init` output) use the
> post-release form `--from code-tribunal`. Until the package is published, substitute the
> git URL — everything else is identical:
>
> ```
> --from "git+https://github.com/arun3676/code-tribunal.git#subdirectory=apps/api"
> ```

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

## Keys: bring any free provider

Tribunal is BYO-key across Groq, Cerebras, and Gemini (all free tiers) — any one key is enough.
Every `tribunal init` emitter can bake keys straight into the block:

```bash
tribunal init openclaw --groq-key gsk_...                       # --key is an alias
tribunal init hermes --cerebras-key csk-... --gemini-key AIza... \
  --providers groq,cerebras,gemini --gemini-model gemini-3.5-flash
```

With no flags you get the classic single-`GROQ_API_KEY` placeholder block (that's what the
committed samples show). After adding keys, run `tribunal doctor` — it reports KEY SET/MISSING
per provider plus a live 1-token PASS/FAIL, and never prints the keys themselves.

## Per-agent guides

- [`openclaw/`](openclaw/) — self-hosted gateway, MCP via `openclaw mcp add`.
- [`hermes/`](hermes/) — autonomous agent (Nous Research), MCP + an [Open Skill](hermes/skill/SKILL.md).

For the full design rationale (why MCP is the spine, and what a deeper native integration
would look like), see the [Architecture section of the main README](../README.md#architecture).
