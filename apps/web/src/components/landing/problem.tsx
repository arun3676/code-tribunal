"use client";

import { Reveal, RevealItem } from "@/components/landing/motion-primitives";

/**
 * "THE GAP" — why the Tribunal exists. Two muted cards (what tooling already
 * covers) and one accent-treated card (the blind spot: intent).
 */

const COVERED = [
  {
    chip: "eslint --fix",
    title: "Linters check style",
    body: "Semicolons, imports, naming. The surface of the code — never what it was supposed to do.",
  },
  {
    chip: "pytest -q · 42 passed",
    title: "Tests check behavior",
    body: "They prove the code does what the code says. Not what the ticket asked for.",
  },
] as const;

export function Problem() {
  return (
    <section aria-labelledby="problem-heading" className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <div className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">The Gap</div>
        <h2 id="problem-heading" className="mt-2 max-w-2xl text-2xl font-semibold leading-tight sm:text-3xl">
          AI writes the code. Nothing checks the ticket.
        </h2>
      </Reveal>

      <Reveal stagger className="mt-8 grid gap-4 sm:grid-cols-3">
        {COVERED.map((card) => (
          <RevealItem key={card.title} className="min-w-0">
            <div className="brutal-sm flex h-full min-w-0 flex-col p-4">
              <span className="inline-block max-w-full self-start overflow-x-auto whitespace-nowrap rounded-md border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-2 py-0.5 font-mono text-[10px] text-fg-dim">
                {card.chip}
              </span>
              <h3 className="mt-3 text-base font-semibold text-fg-muted">{card.title}</h3>
              <p className="mt-1.5 text-[13px] leading-snug text-fg-dim">{card.body}</p>
            </div>
          </RevealItem>
        ))}

        <RevealItem className="min-w-0">
          <div
            className="flex h-full min-w-0 rotate-[-1deg] flex-col rounded-xl border-[2.5px] border-[color:var(--accent)] p-4 text-[color:var(--ink)]"
            style={{
              background: "color-mix(in srgb, var(--accent) 14%, var(--bg-elevated))",
              boxShadow: "3px 3px 0 var(--accent)",
            }}
          >
            <span className="inline-block self-start rounded-md border-2 border-[color:var(--accent)] bg-[color:var(--bg-elevated)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-[color:var(--accent)]">
              the blind spot
            </span>
            <h3 className="mt-3 text-base font-bold">Nobody checks intent</h3>
            <p className="mt-1.5 text-[13px] font-medium leading-snug">
              The ticket said rate-limit login. The diff added logging. Both pass CI.
            </p>
          </div>
        </RevealItem>
      </Reveal>

      <Reveal className="mt-8">
        <p className="font-mono text-[13px] font-bold uppercase tracking-[0.14em] text-fg">
          The Tribunal reads the ticket, cross-examines the diff, and rules.
        </p>
      </Reveal>
    </section>
  );
}
