"use client";

import AgentIntegrations from "@/components/showcase/agent-integrations";
import { Reveal } from "@/components/landing/motion-primitives";
import { useCopyToClipboard } from "@/lib/use-copy";

/**
 * "SHIP IT INTO YOUR AGENT" — headline one-liner install card on top of the
 * existing AgentIntegrations showcase (which carries its own copy blocks).
 */

const INSTALL_CMD = "uvx --from code-tribunal tribunal-mcp";

function HeadlineCommand() {
  const { copied, copy } = useCopyToClipboard();

  return (
    <div className="panel min-w-0 p-4 sm:p-5">
      <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
        {/* overflow-x-auto keeps the long command from busting 390px viewports */}
        <pre className="min-w-0 flex-1 overflow-x-auto rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-3 py-2.5 font-mono text-sm font-bold leading-relaxed text-fg sm:text-base">
          {INSTALL_CMD}
        </pre>
        <button
          onClick={() => copy(INSTALL_CMD)}
          aria-label={copied ? "Copied to clipboard" : "Copy install command to clipboard"}
          className="btn-tactile min-h-[44px] shrink-0 self-start rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-4 py-2 font-mono text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--ink)] sm:self-auto"
        >
          {copied ? "copied" : "copy"}
        </button>
      </div>
      <p className="mt-3 text-[13px] leading-snug text-fg-muted">
        One command. Works in Claude Code, Cursor, Codex, OpenClaw, Hermes — bring your own free Groq/Cerebras/Gemini keys.
      </p>
    </div>
  );
}

export function InstallSection() {
  return (
    <section id="install" aria-labelledby="install-heading" className="mx-auto w-full max-w-6xl scroll-mt-16 px-4 py-16 sm:px-6">
      <Reveal>
        <div className="flex flex-wrap items-center gap-2">
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">Ship It Into Your Agent</div>
          <span className="rounded-full border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-[color:var(--ink)]">
            Coming soon
          </span>
        </div>
        <h2 id="install-heading" className="mt-2 max-w-2xl text-2xl font-semibold leading-tight sm:text-3xl">
          The court travels. Install it where your agent works.
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-fg-muted">
          Here&apos;s how the CLI and MCP server will wire into any coding agent. Publishing
          alongside the hosted court — <a href="#waitlist" className="font-semibold text-fg underline underline-offset-2">join the waitlist</a> to get the install the day it ships.
        </p>
      </Reveal>

      <Reveal className="mt-8">
        <HeadlineCommand />
      </Reveal>

      <Reveal className="mt-6 min-w-0">
        <AgentIntegrations hideHeading />
      </Reveal>
    </section>
  );
}
