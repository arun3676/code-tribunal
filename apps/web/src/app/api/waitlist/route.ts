import { NextResponse } from "next/server";

import { buildWaitlistEmail } from "@/lib/waitlist-email";

/*
 * Waitlist registration — self-contained on Vercel so the landing page works
 * without the Python backend deployed. Signups land in a Resend audience once
 * RESEND_API_KEY + RESEND_AUDIENCE_ID are set; until then they're logged to the
 * function output so early registrations are never lost.
 *
 * Abuse protection (this endpoint triggers Resend-billed email, so it must not
 * be a free relay for spammers):
 *   1. same-origin check — the Origin header must match the request Host;
 *   2. payload cap before parsing;
 *   3. honeypot — the form ships a hidden `website` field humans never fill;
 *      bots that do get a silent 200 and no Resend call;
 *   4. per-IP throttle + a global send budget. Both are per-lambda-instance
 *      (module state resets on cold start and isn't shared across concurrent
 *      instances) — good enough against casual scripted abuse; upgrade path if
 *      real abuse appears is @upstash/ratelimit backed by Redis.
 */

export const runtime = "nodejs";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const MAX_BODY_BYTES = 1024;
const PER_IP_LIMIT = 3;
const PER_IP_WINDOW_MS = 10 * 60 * 1000;
const GLOBAL_SEND_LIMIT = 20;
const GLOBAL_WINDOW_MS = 60 * 60 * 1000;
const MAX_TRACKED_IPS = 500;

const ipHits = new Map<string, number[]>();
let globalSends: number[] = [];

function sameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  if (!origin || !host) return false;
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

function throttled(ip: string): boolean {
  const now = Date.now();
  const hits = (ipHits.get(ip) ?? []).filter((t) => now - t < PER_IP_WINDOW_MS);
  if (hits.length >= PER_IP_LIMIT) {
    ipHits.set(ip, hits);
    return true;
  }
  hits.push(now);
  ipHits.set(ip, hits);
  if (ipHits.size > MAX_TRACKED_IPS) {
    // Drop the oldest-inserted entries so the map can't grow unbounded.
    for (const key of ipHits.keys()) {
      if (ipHits.size <= MAX_TRACKED_IPS) break;
      ipHits.delete(key);
    }
  }
  return false;
}

function sendBudgetExhausted(): boolean {
  const now = Date.now();
  globalSends = globalSends.filter((t) => now - t < GLOBAL_WINDOW_MS);
  if (globalSends.length >= GLOBAL_SEND_LIMIT) return true;
  globalSends.push(now);
  return false;
}

export async function POST(request: Request) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }

  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  if (throttled(ip)) {
    return NextResponse.json(
      { error: "too many requests" },
      { status: 429, headers: { "Retry-After": "600" } },
    );
  }

  let email = "";
  let honeypot = "";
  try {
    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) {
      return NextResponse.json({ error: "payload too large" }, { status: 413 });
    }
    const body = JSON.parse(raw) as { email?: unknown; website?: unknown };
    email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
    honeypot = typeof body.website === "string" ? body.website.trim() : "";
  } catch {
    return NextResponse.json({ error: "invalid body" }, { status: 400 });
  }

  if (honeypot) {
    // A filled honeypot is a bot. Pretend success so it learns nothing.
    return NextResponse.json({ ok: true, stored: "log" });
  }

  if (!EMAIL_RE.test(email) || email.length > 254) {
    return NextResponse.json({ error: "invalid email address" }, { status: 422 });
  }

  const apiKey = process.env.RESEND_API_KEY?.trim();
  const audienceId = process.env.RESEND_AUDIENCE_ID?.trim();

  if (apiKey && audienceId) {
    if (sendBudgetExhausted()) {
      console.warn("waitlist: global send budget exhausted — deferring signup to logs");
      console.log(`waitlist signup (budget-deferred): ${email}`);
      return NextResponse.json({ ok: true, stored: "log" });
    }
    const response = await fetch(`https://api.resend.com/audiences/${audienceId}/contacts`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, unsubscribed: false }),
    });
    // 409 = already registered — success from the visitor's point of view.
    if (!response.ok && response.status !== 409) {
      console.warn(`waitlist: resend rejected signup (status=${response.status})`);
      return NextResponse.json({ error: "signup temporarily unavailable" }, { status: 502 });
    }
    // Serve the summons. Best-effort: a delivery failure (e.g. no verified
    // sending domain yet) must never fail the registration itself.
    await sendSummons(apiKey, email);
    return NextResponse.json({ ok: true, stored: "resend" });
  }

  console.log(`waitlist signup (resend not configured yet): ${email}`);
  return NextResponse.json({ ok: true, stored: "log" });
}

async function sendSummons(apiKey: string, email: string): Promise<void> {
  // Once a domain is verified in Resend, set WAITLIST_FROM to an address on it
  // (e.g. "Clerk of the Court <clerk@yourdomain>"). Until then Resend only
  // delivers from onboarding@resend.dev to the account owner's own address.
  const from = process.env.WAITLIST_FROM?.trim() || "Code Tribunal <onboarding@resend.dev>";
  const { subject, html, text } = buildWaitlistEmail(email);
  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from, to: [email], subject, html, text }),
    });
    if (!res.ok) {
      console.warn(`waitlist: summons email not sent (status=${res.status}) — verify a domain in Resend`);
    }
  } catch (err) {
    console.warn("waitlist: summons email threw", err);
  }
}
