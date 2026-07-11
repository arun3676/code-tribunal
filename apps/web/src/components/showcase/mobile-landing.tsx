"use client";

import Link from "next/link";
import AgentIntegrations from "@/components/showcase/agent-integrations";

const CAPABILITY_CARDS = [
  {
    icon: "⚖️",
    title: "Watch the court deliberate",
    body: "Tap a fixture and watch multiple AI agents reason through the code in real time — streamed, live.",
  },
  {
    icon: "📋",
    title: "Get a merge verdict",
    body: "Did the implementation match the ticket? The Tribunal scores intent-conformance and issues a clear MERGE or BLOCK.",
  },
  {
    icon: "🔍",
    title: "Review any PR",
    body: "Paste a GitHub PR link and let the court check whether the diff actually delivers what the ticket asked for.",
  },
] as const;

export default function MobileLanding() {
  return (
    /* pb-24 bottom clearance for the fixed bottom-tab nav provided by the app shell */
    <main className="space-y-6 px-4 pt-6 pb-24">
      {/* Hero */}
      <section className="panel rounded-2xl p-5">
        <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-fg-muted">
          Code Tribunal
        </div>
        {/* text-[1.6rem] keeps heading from overflowing at 360px; leading-tight improves density */}
        <h1 className="mt-3 text-[1.6rem] font-semibold leading-tight">
          Did the code build what the ticket asked for?
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-fg-muted">
          The Tribunal is a multi-agent intent-conformance court. It reads the
          original ticket, reads the diff, and rules on whether the
          implementation actually delivered — or drifted.
        </p>
        {/* min-h-[44px] ensures touch target ≥44px; w-full so it's easy to tap on narrow screens */}
        <Link
          href="/tribunal"
          className="btn-tactile mt-5 flex min-h-[44px] w-full items-center justify-center rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-5 py-3 font-mono text-sm font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
        >
          Convene a demo →
        </Link>
      </section>

      {/* Capability cards */}
      <section className="space-y-3">
        <div className="px-1 font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">
          What you can do
        </div>
        {CAPABILITY_CARDS.map((card) => (
          <div
            key={card.title}
            /* min-w-0 prevents flex children from overflowing the panel width */
            className="panel flex items-start gap-4 rounded-2xl p-4"
          >
            {/* shrink-0 keeps emoji from squishing when body text is long */}
            <span className="mt-0.5 shrink-0 text-2xl leading-none" aria-hidden="true">
              {card.icon}
            </span>
            <div className="min-w-0">
              <div className="break-words font-semibold text-sm">{card.title}</div>
              <p className="mt-1 break-words text-sm leading-relaxed text-fg-muted">
                {card.body}
              </p>
            </div>
          </div>
        ))}
      </section>

      {/* Agent integrations */}
      <AgentIntegrations />

      {/* Desktop note */}
      <p className="rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-overlay)] px-4 py-3 text-center font-mono text-[11px] uppercase tracking-[0.18em] text-fg-dim">
        The full multi-model code editor is on desktop →
      </p>
    </main>
  );
}
