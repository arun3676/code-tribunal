import { NextResponse } from "next/server";

import { buildWaitlistEmail } from "@/lib/waitlist-email";

/*
 * Waitlist registration — self-contained on Vercel so the landing page works
 * without the Python backend deployed. Signups land in a Resend audience once
 * RESEND_API_KEY + RESEND_AUDIENCE_ID are set; until then they're logged to the
 * function output so early registrations are never lost.
 */

export const runtime = "nodejs";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export async function POST(request: Request) {
  let email = "";
  try {
    const body = (await request.json()) as { email?: unknown };
    email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
  } catch {
    return NextResponse.json({ error: "invalid body" }, { status: 400 });
  }

  if (!EMAIL_RE.test(email) || email.length > 254) {
    return NextResponse.json({ error: "invalid email address" }, { status: 422 });
  }

  const apiKey = process.env.RESEND_API_KEY?.trim();
  const audienceId = process.env.RESEND_AUDIENCE_ID?.trim();

  if (apiKey && audienceId) {
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
