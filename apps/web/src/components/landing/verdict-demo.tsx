"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  m,
  useReducedMotion,
  Reveal,
  SPRING_SLAM,
  EASE_OUT_EXPO,
} from "@/components/landing/motion-primitives";
import { TrustMeter } from "@/components/tribunal/trust-meter";
import { VerdictStamp } from "@/components/tribunal/verdict-stamp";

/*
 * VerdictDemo — a scripted mock trial that plays when scrolled into view.
 * Step timeline (after viewport enter):
 *   1–3  requirements tick green, one by one
 *   4    fourth requirement flags RED + GHOST evidence chip
 *   5    DRIFT evidence chip pops (scope creep)
 *   6    trust meter mounts and fills to 61
 *   7    VerdictStamp slams DOES NOT CONFORM · BLOCK
 * Replay remounts the stage via key. Reduced motion: jump to final state.
 */

const STEP_TIMES_MS = [500, 1100, 1700, 2500, 3600, 4500, 5300];
const FINAL_STEP = STEP_TIMES_MS.length;

const REQUIREMENTS = [
  { id: "R1", text: "Throttle failed attempts per IP (5 / 15 min)", ref: "middleware/ratelimit.py", fail: false },
  { id: "R2", text: "Return HTTP 429 with Retry-After header", ref: "auth/login.py:88", fail: false },
  { id: "R3", text: "Window configurable via settings flag", ref: "settings.py:41", fail: false },
  { id: "R4", text: "Persist lockout counter across restarts", ref: "lockout counter — never written", fail: true },
] as const;

/** Courtroom evidence tag pinned by an agent. */
function EvidenceChip({
  agent,
  charge,
  text,
  personaVar,
  toneVar,
  reduced,
  rotate,
}: {
  agent: string;
  charge: string;
  text: string;
  personaVar: string;
  toneVar: string;
  reduced: boolean;
  rotate: number;
}) {
  return (
    <m.div
      initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.6, rotate: 0 }}
      animate={reduced ? { opacity: 1 } : { opacity: 1, scale: 1, rotate }}
      transition={reduced ? { duration: 0.4 } : SPRING_SLAM}
      className="rounded-xl border-2 border-[color:var(--ink)] bg-elevated p-3"
      style={{ boxShadow: "var(--shadow-ink-sm)" }}
    >
      <div className="flex items-center gap-2">
        <span
          className="rounded-md border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
          style={{ background: `var(${personaVar})` }}
        >
          {agent}
        </span>
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">
          {charge}
        </span>
      </div>
      <p className="mt-2 font-mono text-[11px] font-bold leading-snug" style={{ color: `var(${toneVar})` }}>
        {text}
      </p>
    </m.div>
  );
}

function DemoStage() {
  const reduced = useReducedMotion();
  const [started, setStarted] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!started) return;
    if (reduced) {
      setStep(FINAL_STEP);
      return;
    }
    const timers = STEP_TIMES_MS.map((ms, i) => setTimeout(() => setStep(i + 1), ms));
    return () => timers.forEach(clearTimeout);
  }, [started, reduced]);

  return (
    <m.div
      onViewportEnter={() => setStarted(true)}
      viewport={{ once: true, amount: 0.35 }}
      className="panel grid gap-6 p-5 sm:p-7 md:grid-cols-[1.15fr_1fr] md:gap-8"
    >
      {/* ===== Docket / requirements ===== */}
      <div className="min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span
            className="rounded-md border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em]"
            style={{ background: "var(--clerk)" }}
          >
            Docket
          </span>
          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">
            LOGIN-482 · 4 requirements
          </span>
        </div>
        <h3 className="mt-3 text-lg font-bold leading-snug text-fg sm:text-xl">
          Add rate limiting to the login endpoint
        </h3>

        <ul className="mt-4 space-y-2.5">
          {REQUIREMENTS.map((req, i) => {
            const resolved = step >= i + 1;
            const failed = req.fail && resolved;
            const passed = !req.fail && resolved;
            return (
              <li
                key={req.id}
                className="flex items-start gap-3 rounded-xl border-2 p-3 transition-colors duration-300"
                style={{
                  borderColor: failed
                    ? "var(--danger)"
                    : passed
                      ? "var(--ink)"
                      : "color-mix(in srgb, var(--ink) 25%, transparent)",
                  background: failed
                    ? "color-mix(in srgb, var(--danger) 9%, #ffffff)"
                    : passed
                      ? "var(--bg-overlay)"
                      : "transparent",
                }}
              >
                <span
                  className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border-2 font-mono text-xs font-bold"
                  style={{
                    borderColor: resolved ? (failed ? "var(--danger)" : "var(--accent)") : "var(--fg-dim)",
                    color: failed ? "var(--danger)" : "var(--accent)",
                    background: resolved
                      ? failed
                        ? "color-mix(in srgb, var(--danger) 14%, #ffffff)"
                        : "color-mix(in srgb, var(--accent) 14%, #ffffff)"
                      : "transparent",
                  }}
                >
                  {resolved ? (
                    <m.span
                      initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.4 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={reduced ? { duration: 0.3 } : SPRING_SLAM}
                    >
                      {failed ? "✕" : "✓"}
                    </m.span>
                  ) : (
                    <span className="text-fg-dim">·</span>
                  )}
                </span>
                <div className="min-w-0">
                  <p
                    className="text-sm font-semibold leading-snug"
                    style={{ color: failed ? "var(--danger)" : "var(--fg)" }}
                  >
                    {req.text}
                  </p>
                  <p
                    className="mt-0.5 truncate font-mono text-[10px] uppercase tracking-[0.08em]"
                    style={{ color: failed ? "var(--danger)" : "var(--fg-dim)" }}
                  >
                    {resolved ? req.ref : "under examination…"}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {/* ===== Verdict column ===== */}
      <div className="flex min-w-0 flex-col gap-3 md:min-h-[26rem]">
        <div className="flex items-center justify-between gap-2">
          <span
            className="rounded-md border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em]"
            style={{ background: "var(--arbiter)" }}
          >
            Verdict
          </span>
          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">
            {step >= FINAL_STEP ? "ruling entered" : "court in session…"}
          </span>
        </div>

        {step >= 4 && (
          <EvidenceChip
            agent="GHOST"
            charge="Omission"
            text="lockout counter — never written"
            personaVar="--ghost"
            toneVar="--danger"
            reduced={!!reduced}
            rotate={-1.5}
          />
        )}
        {step >= 5 && (
          <EvidenceChip
            agent="DRIFT"
            charge="Scope creep"
            text="unrequested logging refactor in auth/session.py"
            personaVar="--drift"
            toneVar="--warning"
            reduced={!!reduced}
            rotate={1.5}
          />
        )}

        {step >= 6 && (
          <m.div
            initial={reduced ? { opacity: 0 } : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: EASE_OUT_EXPO }}
            className="brutal-flat mt-1 p-3"
          >
            {/* Mounted late so TrustMeter's CSS fill animation plays on cue */}
            <TrustMeter score={61} />
          </m.div>
        )}

        {/* VerdictStamp's own .stamp-press CSS animation supplies the slam on mount */}
        <div className="min-h-[9rem] sm:min-h-[11rem]">
          {step >= 7 && <VerdictStamp state="DOES_NOT_CONFORM" merge="BLOCK" />}
        </div>
      </div>
    </m.div>
  );
}

export function VerdictDemo() {
  const [runId, setRunId] = useState(0);

  return (
    <section id="demo" className="scroll-mt-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">
          Exhibit — mock trial
        </p>
        <h2 className="mt-3 text-3xl font-bold tracking-tight text-fg sm:text-4xl">
          Watch a verdict land
        </h2>
        <p className="mt-3 text-base leading-relaxed text-fg-muted">
          A real docket, scripted — no API calls.
        </p>
      </Reveal>

      <div className="mt-10">
        <DemoStage key={runId} />
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={() => setRunId((n) => n + 1)}
          className="btn-tactile inline-flex min-h-[44px] items-center justify-center rounded-xl border-2 border-[color:var(--ink)] bg-elevated px-6 py-3 font-mono text-sm font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
        >
          ↺ Replay
        </button>
        <Link
          href="/tribunal"
          className="btn-tactile inline-flex min-h-[44px] items-center justify-center rounded-xl border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-6 py-3 font-mono text-sm font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
        >
          Run it on a real PR →
        </Link>
      </div>
    </section>
  );
}
