# Code Tribunal × Hermes

[Hermes](https://hermes-agent.nousresearch.com/docs/) (Nous Research) is an autonomous agent
that runs persistently across local, Docker, SSH, Daytona, Singularity, and Modal backends.
It is an MCP client with first-class tool filtering, and it speaks the **Open Skills** standard.

## Add the MCP server

Drop this into `~/.hermes/config.yaml` (verbatim in [`config.yaml`](config.yaml), or
`tribunal init hermes`), then run `/reload-mcp`:

```yaml
mcp_servers:
  tribunal:
    command: "uvx"
    args: ["--from", "code-tribunal", "tribunal-mcp"]
    env:
      GROQ_API_KEY: "<your GROQ_API_KEY>"
    tools:
      include: [verify_intent_conformance, ghost_check, drift_check]
    enabled: true
```

`GROQ_API_KEY` is only the default — any free key works (Groq / Cerebras / Gemini). Use
`tribunal init hermes --groq-key ... --cerebras-key ... --gemini-key ...
--providers groq,cerebras,gemini` (with optional `--groq-model` / `--cerebras-model` /
`--gemini-model` overrides) to emit a multi-provider `env` block, and `tribunal doctor` to
verify the keys actually work (it never prints them).

### Cost tuning with `tools.include`

The fast checks (`ghost_check`, `drift_check`) are deterministic — no LLM round-trip. On a
small VPS you can expose only those and keep the full court off:

```yaml
    tools:
      include: [ghost_check, drift_check]
```

Run the full `verify_intent_conformance` on heavier backends (Modal / Daytona).

## Teach the loop: the Open Skill

The MCP server makes the tools *available*; the [Open Skill](skill/SKILL.md) makes the agent
*know to use them*. It encodes the write → verify → fix procedure so, riding Hermes' procedural
memory, the gate becomes a learned habit instead of a one-off prompt.
