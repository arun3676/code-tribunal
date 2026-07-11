"use client";

import { FormEvent, useState } from "react";

import { joinWaitlist } from "@/lib/api";
import { m, Reveal, SPRING_SLAM } from "@/components/landing/motion-primitives";

/**
 * "Coming soon" invite registration — the closing section of the landing page.
 * The CLI + MCP ship today; the hosted court is invite-first. Registrations go
 * to the /waitlist API (Resend audience once the key is configured).
 */

type FormState = "idle" | "sending" | "done" | "error";

export function Waitlist() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<FormState>("idle");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "sending") return;
    // Honeypot: uncontrolled hidden field — bots autofill it, humans never see it.
    const honeypot = String(new FormData(event.currentTarget).get("website") ?? "");
    setState("sending");
    try {
      await joinWaitlist(email.trim(), honeypot.trim());
      setState("done");
    } catch {
      setState("error");
    }
  }

  return (
    <section
      id="waitlist"
      aria-labelledby="waitlist-heading"
      className="mx-auto w-full max-w-6xl scroll-mt-16 px-4 py-16 sm:px-6"
    >
      <Reveal>
        <div className="panel rounded-2xl p-6 sm:p-8">
          <div className="grid gap-8 lg:grid-cols-[1.2fr_1fr] lg:items-center">
            <div>
              <div className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">
                Coming Soon
              </div>
              <h2 id="waitlist-heading" className="mt-2 text-2xl font-semibold leading-tight sm:text-3xl">
                The hosted court is next. Get on the docket.
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-fg-muted">
                The CLI and MCP server ship today, free, with your own keys. The hosted
                court — team dashboards, a PR bot, verdict history — opens invite-first.
                Register and your invitation lands the day it does.
              </p>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-fg-muted">
                We&apos;re not a model lab. We&apos;re the layer between the ticket and the
                diff — and because the court reasons with whatever key you bring, it gets
                sharper with every model upgrade. <span className="font-semibold text-fg">Your
                keys, your models, our courtroom.</span>
              </p>
            </div>

            <div className="min-w-0">
              {state === "done" ? (
                <m.div
                  initial={{ scale: 1.6, opacity: 0, rotate: -6 }}
                  animate={{ scale: 1, opacity: 1, rotate: -2 }}
                  transition={SPRING_SLAM}
                  className="mx-auto flex h-36 w-36 flex-col items-center justify-center rounded-full border-4 border-double border-[color:var(--accent)] text-center sm:h-40 sm:w-40"
                  role="status"
                >
                  <span className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-[color:var(--accent)]">
                    Tribunal
                  </span>
                  <span className="font-mono text-sm font-bold uppercase tracking-[0.12em] text-[color:var(--accent)]">
                    On the docket
                  </span>
                  <span className="mt-1 rounded border-2 border-[color:var(--accent)] px-1.5 font-mono text-[10px] font-bold uppercase text-[color:var(--accent)]">
                    Invite pending
                  </span>
                </m.div>
              ) : (
                <form onSubmit={onSubmit} className="flex min-w-0 flex-col gap-3">
                  {/* Honeypot — visually hidden and skipped by keyboard/screen readers. */}
                  <input
                    type="text"
                    name="website"
                    tabIndex={-1}
                    autoComplete="off"
                    aria-hidden="true"
                    className="absolute -left-[9999px] h-px w-px opacity-0"
                    defaultValue=""
                  />
                  <label
                    htmlFor="waitlist-email"
                    className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-fg-muted"
                  >
                    Email for your invite
                  </label>
                  <div className="flex min-w-0 flex-col gap-3 sm:flex-row">
                    <input
                      id="waitlist-email"
                      type="email"
                      required
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      placeholder="you@yourteam.dev"
                      autoComplete="email"
                      className="min-h-[48px] min-w-0 flex-1 rounded-xl border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-4 font-mono text-sm text-fg placeholder:text-fg-dim focus:outline-none focus:ring-2 focus:ring-[color:var(--accent)]"
                    />
                    <button
                      type="submit"
                      disabled={state === "sending"}
                      className="btn-tactile min-h-[48px] shrink-0 rounded-xl border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-6 font-mono text-sm font-bold uppercase tracking-[0.16em] text-[color:var(--ink)] disabled:opacity-60"
                    >
                      {state === "sending" ? "Filing…" : "Request invite"}
                    </button>
                  </div>
                  {state === "error" ? (
                    <p className="font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-danger" role="alert">
                      Filing failed — check the address and try again.
                    </p>
                  ) : (
                    <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-fg-dim">
                      No spam. One invitation, when the court opens.
                    </p>
                  )}
                </form>
              )}
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
