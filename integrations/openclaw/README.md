# Code Tribunal × OpenClaw

[OpenClaw](https://docs.openclaw.ai/) is a self-hosted gateway that bridges chat apps to an
agent runtime with native MCP support. Tribunal plugs in as an MCP server.

## Add it

```bash
openclaw mcp add tribunal \
  --command uvx \
  --arg --from --arg code-tribunal --arg tribunal-mcp
```

…which persists into `~/.openclaw/openclaw.json`. The exact block is in
[`openclaw.json`](openclaw.json) (also: `tribunal init openclaw`):

```json
{
  "mcp": {
    "servers": {
      "tribunal": {
        "command": "uvx",
        "args": ["--from", "code-tribunal", "tribunal-mcp"],
        "env": { "GROQ_API_KEY": "<your GROQ_API_KEY>" }
      }
    }
  }
}
```

Groq is just the default: any free key works (Groq / Cerebras / Gemini). Bake real keys in
with `tribunal init openclaw --groq-key ... --cerebras-key ... --gemini-key ...
--providers groq,cerebras,gemini` (plus optional `--groq-model` / `--cerebras-model` /
`--gemini-model` overrides), then run `tribunal doctor` to confirm at least one provider
answers — it never prints your keys.

## Use it

Once registered, an OpenClaw agent can call `verify_intent_conformance`, `ghost_check`, and
`drift_check` mid-task. A reviewer agent can post the verdict straight back into the Discord /
Slack thread the ticket came from, and gate before a human ever sees the diff. On a `BLOCK`
verdict, the agent should fix the named blockers and re-verify rather than declaring success.
