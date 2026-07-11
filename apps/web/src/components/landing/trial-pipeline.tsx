"use client";

import { useRef } from "react";
import { useScroll, useTransform } from "motion/react";
import { m, Reveal, EASE_OUT_EXPO, useReducedMotion } from "@/components/landing/motion-primitives";
import { AgentAvatar } from "@/components/tribunal/agent-avatar";
import { PERSONAS } from "@/components/tribunal/personas";
import type { AgentName } from "@/lib/api";

/**
 * "HOW A TRIAL RUNS" — the seven stages in trial order along a scroll-linked
 * progress rail. Desktop: horizontal rail (scaleX, origin left). Mobile:
 * vertical spine on the left edge (scaleY, origin top). WARDEN is the dashed
 * conditional stage. Reduced motion: rail renders full, nodes fade only.
 */

type Stage = { agent: AgentName; duty: string; conditional?: boolean };

const STAGES: Stage[] = [
  { agent: "CLERK", duty: "Files the case, summons the court." },
  { agent: "ADVOCATE", duty: "Turns the ticket into hard requirements." },
  { agent: "SURVEYOR", duty: "Maps what the diff actually shipped." },
  { agent: "GHOST", duty: "Finds what was asked but never written." },
  { agent: "DRIFT", duty: "Flags changes nobody authorized." },
  { agent: "WARDEN", duty: "Recruited when auth or payments appear.", conditional: true },
  { agent: "ARBITER", duty: "Weighs every witness. Issues the ruling." },
];

export function TrialPipeline() {
  const ref = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion() ?? false;

  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 0.8", "end 0.5"] });
  const railScale = useTransform(scrollYProgress, [0, 1], [0, 1]);

  return (
    <section aria-labelledby="pipeline-heading" className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <div className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">How a Trial Runs</div>
        <h2 id="pipeline-heading" className="mt-2 max-w-2xl text-2xl font-semibold leading-tight sm:text-3xl">
          Ticket in. Cross-examination. Verdict out.
        </h2>
      </Reveal>

      <div ref={ref} className="relative mt-10">
        {/* Desktop rail — horizontal, behind the avatar row */}
        <div aria-hidden="true" className="absolute left-8 right-8 top-[21px] hidden h-[3px] rounded-full bg-[color:var(--ink)] opacity-15 md:block" />
        <m.div
          aria-hidden="true"
          className="absolute left-8 right-8 top-[21px] hidden h-[3px] origin-left rounded-full bg-[color:var(--accent)] md:block"
          style={{ scaleX: reduced ? 1 : railScale }}
        />

        {/* Mobile rail — vertical spine along the left edge */}
        <div aria-hidden="true" className="absolute bottom-6 left-[20px] top-6 w-[3px] rounded-full bg-[color:var(--ink)] opacity-15 md:hidden" />
        <m.div
          aria-hidden="true"
          className="absolute bottom-6 left-[20px] top-6 w-[3px] origin-top rounded-full bg-[color:var(--accent)] md:hidden"
          style={{ scaleY: reduced ? 1 : railScale }}
        />

        <ol className="relative flex flex-col gap-7 md:grid md:grid-cols-7 md:gap-3">
          {STAGES.map((stage, i) => {
            const p = PERSONAS[stage.agent];
            return (
              <m.li
                key={stage.agent}
                initial={{ opacity: 0, scale: reduced ? 1 : 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, amount: 0.6 }}
                transition={{ duration: 0.45, ease: EASE_OUT_EXPO, delay: reduced ? 0 : i * 0.07 }}
                className="flex min-w-0 items-start gap-3 md:flex-col md:items-center md:text-center"
              >
                <span
                  className={`shrink-0 rounded-full ${stage.conditional ? "border-2 border-dashed border-[color:var(--danger)] p-[2px]" : ""}`}
                >
                  <AgentAvatar agent={stage.agent} size={40} active />
                </span>
                <div className="min-w-0 md:mt-1.5">
                  <div className="font-mono text-xs font-bold tracking-[0.14em]">
                    {stage.agent}
                    {stage.conditional ? <span className="text-[color:var(--danger)]"> ?</span> : null}
                  </div>
                  <p className="mt-0.5 text-[11px] leading-snug text-fg-muted">{stage.duty}</p>
                  {stage.conditional ? (
                    <span className="mt-1 inline-block rounded border-2 border-dashed border-[color:var(--danger)] px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase tracking-[0.12em] text-[color:var(--danger)]">
                      conditional
                    </span>
                  ) : null}
                  <span className="sr-only">{p.role}</span>
                </div>
              </m.li>
            );
          })}
        </ol>
      </div>

      <Reveal className="mt-10">
        <div className="brutal-sm mx-auto max-w-2xl border-l-[7px] p-4" style={{ borderLeftColor: "var(--arbiter)" }}>
          <p className="font-mono text-[12px] font-bold uppercase tracking-[0.14em] leading-relaxed">
            Deterministic scoring — 100 minus earned deductions. Same inputs, same verdict.
          </p>
        </div>
      </Reveal>
    </section>
  );
}
