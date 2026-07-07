"use client";

import { m, Reveal, RevealItem, SPRING_SLAM, useReducedMotion } from "@/components/landing/motion-primitives";
import { AgentAvatar } from "@/components/tribunal/agent-avatar";
import { PERSONAS, TRIAL_ORDER } from "@/components/tribunal/personas";

/**
 * "MEET THE COURT" — all seven personas as pastel sticker cards in trial
 * order. Mobile: horizontal snap-scroll row. md+: 4-up grid (4 + 3).
 * Catchphrases pop in as speech bubbles on scroll (SPRING_SLAM).
 */

function SpeechBubble({ text, reduced }: { text: string; reduced: boolean }) {
  return (
    <m.div
      variants={{
        hidden: { opacity: 0, scale: reduced ? 1 : 0.6 },
        visible: { opacity: 1, scale: 1, transition: reduced ? { duration: 0.3 } : SPRING_SLAM },
      }}
      style={{ transformOrigin: "bottom left" }}
      className="relative mt-3"
    >
      <p className="rounded-lg rounded-bl-none border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-2.5 py-1.5 text-[11px] font-bold leading-snug">
        “{text}”
      </p>
      {/* tail */}
      <span
        aria-hidden="true"
        className="absolute -bottom-[7px] left-2 h-3 w-3 rotate-45 border-b-2 border-r-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)]"
        style={{ clipPath: "polygon(100% 0, 100% 100%, 0 100%)" }}
      />
    </m.div>
  );
}

export function CourtRoster() {
  const reduced = useReducedMotion() ?? false;

  return (
    <section aria-labelledby="roster-heading" className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <div className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">Meet the Court</div>
        <h2 id="roster-heading" className="mt-2 max-w-2xl text-2xl font-semibold leading-tight sm:text-3xl">
          Seven agents. One verdict.
        </h2>
      </Reveal>

      <Reveal
        stagger
        className="-mx-4 mt-8 flex snap-x snap-mandatory gap-4 overflow-x-auto px-4 pb-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:-mx-6 sm:px-6 md:mx-0 md:grid md:snap-none md:grid-cols-4 md:overflow-visible md:px-0 md:pb-0"
      >
        {TRIAL_ORDER.map((agent) => {
          const p = PERSONAS[agent];
          return (
            <RevealItem key={agent} className="w-[240px] shrink-0 snap-start md:w-auto">
              <div
                className="flex h-full min-w-0 flex-col rounded-2xl border-[2.5px] border-[color:var(--ink)] p-3 text-[color:var(--ink)]"
                style={{
                  background: `color-mix(in srgb, ${p.color} 38%, #ffffff)`,
                  boxShadow: "var(--shadow-ink-sm)",
                }}
              >
                <div className="flex items-center gap-2.5">
                  <span className="shrink-0">
                    <AgentAvatar agent={agent} size={44} active />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-mono text-sm font-bold tracking-[0.12em]">{agent}</div>
                    <div className="truncate text-[11px] font-semibold italic opacity-80">“{p.nickname}”</div>
                  </div>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  <span className="inline-block rounded-full border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider">
                    {p.role}
                  </span>
                  {p.recruited ? (
                    <span className="inline-block rounded-full border-2 border-dashed border-[color:var(--danger)] bg-[color:var(--bg-elevated)] px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider text-[color:var(--danger)]">
                      recruited mid-trial
                    </span>
                  ) : null}
                </div>

                <p className="mt-2 flex-1 text-[11px] font-medium leading-snug">{p.tagline}</p>

                <SpeechBubble text={p.catchphrase} reduced={reduced} />
              </div>
            </RevealItem>
          );
        })}
      </Reveal>
    </section>
  );
}
