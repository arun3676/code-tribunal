"use client";

import { useState } from "react";

type Integration = {
  tag: string;
  title: string;
  color: string; // persona accent, used for the card's left rail + badge
  blurb: string;
  codeLabel: string;
  code: string;
  foot?: string;
};

const INTEGRATIONS: Integration[] = [
  {
    tag: "Shell · CI",
    title: "CLI",
    color: "var(--arbiter)",
    blurb: "Gate any PR from your terminal or pipeline. Exit 0 = clear to merge, 1 = blocked — drop it straight into CI.",
    codeLabel: "gate a PR, exit-code only",
    code: "tribunal verify --ticket ticket.md --git --quiet || exit 1",
  },
  {
    tag: "Any MCP client",
    title: "MCP server",
    color: "var(--clerk)",
    blurb: "One server, every MCP-native agent. Registers verify / ghost / drift as tools your agent calls mid-task.",
    codeLabel: "Claude Code · Cursor (mcpServers)",
    code: `{
  "mcpServers": {
    "tribunal": {
      "command": "uvx",
      "args": ["--from", "code-tribunal", "tribunal-mcp"],
      "env": { "GROQ_API_KEY": "<your-key>" }
    }
  }
}`,
  },
  {
    tag: "Self-hosted gateway",
    title: "OpenClaw",
    color: "var(--advocate)",
    blurb: "Add the gate to your OpenClaw agent and post verdicts straight back into the Discord / Slack thread the ticket came from.",
    codeLabel: "openclaw mcp add",
    code: `openclaw mcp add tribunal \\
  --command uvx \\
  --arg --from --arg code-tribunal --arg tribunal-mcp`,
  },
  {
    tag: "Autonomous agent",
    title: "Hermes",
    color: "var(--drift)",
    blurb: "MCP plus an Open Skill that teaches the write → verify → fix loop, so the gate becomes a habit across sessions.",
    codeLabel: "generate the ~/.hermes block",
    code: "tribunal init hermes",
    foot: "Bundled Open Skill: integrations/hermes/skill",
  },
];

function CopyBlock({ code, label }: { code: string; label: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      /* clipboard unavailable (e.g. insecure context) — no-op */
    }
  }

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2">
        {/* min-w-0 + truncate prevents label from overflowing flex row */}
        <span className="min-w-0 truncate font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-fg-dim">{label}</span>
        {/* min-h-[40px] min-w-[56px] ensures touch target ≥40px on mobile */}
        <button
          onClick={copy}
          aria-label={copied ? "Copied to clipboard" : "Copy to clipboard"}
          className="btn-tactile min-h-[40px] min-w-[56px] shrink-0 rounded-md border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-fg"
        >
          {copied ? "copied" : "copy"}
        </button>
      </div>
      {/* overflow-x-auto + max-w-full prevents pre from busting card bounds on narrow viewports */}
      <pre className="max-w-full overflow-x-auto rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-2.5 py-2 font-mono text-[10px] leading-relaxed text-fg">
        {code}
      </pre>
    </div>
  );
}

export default function AgentIntegrations() {
  return (
    <section className="panel rounded-2xl p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-fg-muted">Ship it into your agent</div>
          <h2 className="mt-2 text-2xl font-semibold">Wire the Tribunal into any coding agent.</h2>
          <p className="mt-2 max-w-3xl text-sm text-fg-muted">
            The same intent-conformance court that runs in this browser ships as a CLI and an MCP server. Both{" "}
            <span className="font-semibold text-fg">OpenClaw</span> and{" "}
            <span className="font-semibold text-fg">Hermes</span> are MCP clients — so an agent can ask
            “does this diff match the ticket?” and loop on <span className="font-mono text-fg">BLOCK</span> before a human ever sees it.
          </p>
        </div>
        <code className="rounded-md border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-2.5 py-1 font-mono text-[11px] text-fg">
          tribunal init &lt;agent&gt;
        </code>
      </div>

      {/* 1→2→4 responsive grid; lg step (640-1023px tablet) stays at 2 cols */}
      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {INTEGRATIONS.map((item) => (
          <div
            key={item.title}
            /* min-w-0 prevents card from overflowing its grid column */
            className="panel flex min-w-0 flex-col rounded-2xl p-4"
            style={{ borderLeftWidth: "7px", borderLeftColor: item.color }}
          >
            <div className="flex items-start justify-between gap-2">
              {/* font-semibold title — allow wrapping so long names don't overflow */}
              <h3 className="break-words text-base font-semibold leading-snug">{item.title}</h3>
              {/* shrink-0 keeps the badge from collapsing */}
              <span
                className="mt-0.5 shrink-0 rounded-full border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[color:var(--ink)]"
                style={{ background: `color-mix(in srgb, ${item.color} 45%, #ffffff)` }}
              >
                {item.tag}
              </span>
            </div>
            <p className="mt-2 flex-1 text-[13px] leading-snug text-fg-muted">{item.blurb}</p>
            <div className="mt-3 min-w-0">
              <CopyBlock code={item.code} label={item.codeLabel} />
              {item.foot ? (
                <p className="mt-1.5 break-words font-mono text-[9px] uppercase tracking-[0.14em] text-fg-dim">{item.foot}</p>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <a
          href="/about"
          className="btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-4 py-2 font-mono text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--ink)]"
        >
          How it works
        </a>
        <span className="text-[11px] text-fg-dim">
          Three tools: <span className="font-mono text-fg-muted">verify_intent_conformance</span> ·{" "}
          <span className="font-mono text-fg-muted">ghost_check</span> ·{" "}
          <span className="font-mono text-fg-muted">drift_check</span>
        </span>
      </div>
    </section>
  );
}
