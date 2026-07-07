"use client";

import type { AgentName } from "@/lib/api";
import { AgentAvatar } from "./agent-avatar";
import { PERSONAS } from "./personas";

/**
 * Bold pastel "sticker" character card — solid persona fill, thick black
 * border, hard offset shadow, all-black text. Introduces each agent's
 * personality so the cast reads instantly in the demo.
 */
export function AgentCard({ agent }: { agent: AgentName }) {
  const p = PERSONAS[agent];
  return (
    <div
      className="btn-tactile group relative overflow-hidden rounded-2xl border-[2.5px] border-[color:var(--ink)] p-3 text-[color:var(--ink)]"
      style={{ background: `color-mix(in srgb, ${p.color} 38%, #ffffff)` }}
    >
      {/* watermark avatar */}
      <div className="pointer-events-none absolute -right-3 -top-3 opacity-20 transition-opacity group-hover:opacity-30">
        <AgentAvatar agent={agent} size={84} />
      </div>

      <div className="flex items-center gap-2.5">
        <span className="shrink-0">
          <AgentAvatar agent={agent} size={46} active />
        </span>
        <div className="min-w-0 flex-1">
          <div className="font-mono text-sm font-bold tracking-[0.12em]">{agent}</div>
          <div className="truncate text-[11px] font-semibold italic opacity-80">“{p.nickname}”</div>
        </div>
      </div>

      <div className="mt-2 inline-block rounded-full border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider">
        {p.role}
      </div>

      <p className="mt-2 text-[11px] font-medium leading-snug">{p.tagline}</p>

      <p className="mt-2 border-t-2 border-[color:var(--ink)] border-dotted pt-2 text-[11px] font-bold leading-snug">“{p.catchphrase}”</p>

      <div className="mt-2 flex flex-wrap items-center justify-between gap-1">
        <span className="font-mono text-[10px] font-bold uppercase tracking-wider opacity-70">{p.provider}</span>
        {p.recruited ? <span className="rounded border-2 border-[color:var(--ink)] bg-[color:var(--warden)] px-1 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider">recruited live</span> : null}
      </div>
    </div>
  );
}
