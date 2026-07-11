"use client";

import { useEffect, useState } from "react";

import {
  m,
  useReducedMotion,
  SPRING_SLAM,
  EASE_OUT_EXPO,
} from "@/components/landing/motion-primitives";
import { TrustMeter } from "@/components/tribunal/trust-meter";

/*
 * Hero — "The Gavel Drop".
 * The headline is SSR-visible (no opacity-0 on text); only the evidence stage
 * (ticket panel, diff panel, stamp, meter) runs the entrance timeline:
 *   0.25s ticket slides in from the left
 *   0.65s diff slides in from the right
 *   1.25s verdict stamp slams down (SPRING_SLAM)
 *   1.50s trust meter mounts and fills to 87
 * Reduced motion: everything fades, no transforms, no delays.
 */

const DIFF_LINES = [
  { sign: "+", text: "limiter = RateLimiter(max_attempts=5)" },
  { sign: "+", text: "if limiter.exceeded(ip): return 429" },
  { sign: "-", text: "return handle_login(request)" },
] as const;

/**
 * Lightweight lookalike of tribunal/verdict-stamp.tsx. The real VerdictStamp
 * hard-codes its own `.stamp-press` CSS entrance, which would compound with
 * the m.div SPRING_SLAM here — so we reuse its exact classes/styles minus the
 * animation class and let motion drive the slam.
 */
function HeroStamp() {
  const c = "var(--accent)";
  return (
    <div
      className="relative flex h-28 w-28 flex-col items-center justify-center rounded-full bg-white text-center sm:h-32 sm:w-32"
      style={{
        border: `4px double ${c}`,
        color: c,
        background: `color-mix(in srgb, ${c} 12%, #ffffff)`,
        boxShadow: `0 0 0 2px ${c}`,
      }}
    >
      <div
        className="absolute inset-1.5 rounded-full border-2"
        style={{ borderColor: `color-mix(in srgb, ${c} 55%, transparent)` }}
      />
      <span className="font-mono text-[9px] font-bold uppercase tracking-[0.25em] opacity-80">
        Tribunal
      </span>
      <span className="mt-1 px-1 font-mono text-[12px] font-bold leading-tight">CONFORMS</span>
      <span
        className="mt-1.5 rounded-sm border-2 px-1.5 py-0.5 font-mono text-[10px] font-bold tracking-widest"
        style={{ borderColor: c }}
      >
        APPROVE
      </span>
    </div>
  );
}

export function Hero() {
  const reduced = useReducedMotion();
  // 0 = panels animating in, 1 = stamp slammed, 2 = meter filling
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    if (reduced) {
      setPhase(2);
      return;
    }
    const t1 = setTimeout(() => setPhase(1), 1250);
    const t2 = setTimeout(() => setPhase(2), 1500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [reduced]);

  const slideIn = (fromX: number, delay: number) => ({
    initial: reduced ? { opacity: 0 } : { opacity: 0, x: fromX },
    animate: { opacity: 1, x: 0 },
    transition: reduced
      ? { duration: 0.3, delay: 0 }
      : { duration: 0.7, ease: EASE_OUT_EXPO, delay },
  });

  return (
    <section className="relative overflow-x-clip">
      <div className="mx-auto flex min-h-[88svh] w-full max-w-6xl flex-col items-center justify-center gap-12 px-4 py-16 lg:flex-row lg:gap-14">
        {/* ===== Copy column (SSR-visible, no entrance opacity) ===== */}
        <div className="w-full min-w-0 max-w-xl lg:flex-1">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">
            Code Tribunal — The court for AI-generated code
          </p>
          <h1 className="mt-4 text-4xl font-bold leading-[1.06] tracking-tight text-fg sm:text-5xl lg:text-6xl">
            Did the code build what{" "}
            <span className="relative inline-block">
              the ticket
              <span
                aria-hidden="true"
                className="absolute inset-x-0 bottom-1 -z-10 h-3 -rotate-1 rounded-sm sm:h-4"
                style={{ background: "var(--arbiter)" }}
              />
            </span>{" "}
            asked for?
          </h1>
          <p className="mt-5 max-w-lg text-base leading-relaxed text-fg-muted sm:text-lg">
            Linters check style. Tests check behavior. The Tribunal checks{" "}
            <strong className="font-semibold text-fg">intent</strong> — seven agents cross-examine
            every diff against the ticket and stamp a verdict.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <a
              href="#demo"
              className="btn-tactile inline-flex min-h-[44px] items-center justify-center rounded-xl border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-6 py-3 font-mono text-sm font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
            >
              See the court rule →
            </a>
            <a
              href="#waitlist"
              className="btn-tactile inline-flex min-h-[44px] items-center justify-center rounded-xl border-2 border-[color:var(--ink)] bg-elevated px-6 py-3 font-mono text-sm font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
            >
              Get early access
            </a>
          </div>

          <p className="mt-5 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-fg-dim">
            CLI · MCP · Web — free-tier LLMs, bring your own keys
          </p>
        </div>

        {/* ===== Evidence stage ===== */}
        <div className="relative w-full min-w-0 max-w-md lg:max-w-lg lg:flex-1" aria-hidden="true">
          {/* Ticket exhibit */}
          <m.div {...slideIn(-60, 0.25)} className="panel relative z-10 -rotate-1 p-4 sm:p-5">
            <div className="flex items-center justify-between gap-2">
              <span
                className="rounded-md border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em]"
                style={{ background: "var(--clerk)" }}
              >
                Ticket
              </span>
              <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">
                LOGIN-482
              </span>
            </div>
            <p className="mt-3 text-base font-semibold leading-snug text-fg">
              Add rate limiting to login
            </p>
            <ul className="mt-2 space-y-1 font-mono text-[11px] leading-relaxed text-fg-muted">
              <li>· max 5 attempts / 15 min per IP</li>
              <li>· return 429 with Retry-After</li>
            </ul>
          </m.div>

          {/* Diff exhibit */}
          <m.div
            {...slideIn(60, 0.65)}
            className="brutal-sm relative z-20 -mt-2 ml-6 rotate-1 p-4 sm:ml-10 sm:p-5"
          >
            <div className="flex items-center justify-between gap-2">
              <span
                className="rounded-md border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em]"
                style={{ background: "var(--surveyor)" }}
              >
                Diff
              </span>
              <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">
                auth/login.py
              </span>
            </div>
            <div className="mt-3 overflow-x-auto whitespace-pre font-mono text-[11px] leading-relaxed">
              {DIFF_LINES.map((line) => (
                <div
                  key={line.text}
                  className="rounded-sm px-1.5"
                  style={{
                    color: line.sign === "+" ? "var(--accent)" : "var(--danger)",
                    background:
                      line.sign === "+" ? "rgba(15, 157, 99, 0.1)" : "rgba(226, 60, 78, 0.1)",
                  }}
                >
                  {line.sign} {line.text}
                </div>
              ))}
            </div>
          </m.div>

          {/* Verdict stamp slams over the seam of the two exhibits */}
          <div className="pointer-events-none absolute -top-4 right-0 z-30 sm:-right-3 sm:-top-6">
            {phase >= 1 && (
              <m.div
                initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 2.2, rotate: -8 }}
                animate={reduced ? { opacity: 1 } : { opacity: 1, scale: 1, rotate: -3 }}
                transition={reduced ? { duration: 0.4 } : SPRING_SLAM}
              >
                <HeroStamp />
              </m.div>
            )}
          </div>

          {/* Trust meter — mounts after the stamp so its CSS fill plays visibly */}
          <div className="mt-5 min-h-[6.5rem]">
            {phase >= 2 && (
              <m.div
                initial={reduced ? { opacity: 0 } : { opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: EASE_OUT_EXPO }}
                className="brutal-sm p-4"
              >
                <TrustMeter score={87} />
              </m.div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
