/*
 * The "summons" — a funny, courtroom-themed welcome email sent to each person
 * who registers for early access. Plain inline-styled HTML (email clients strip
 * <style>/external CSS and rarely load web fonts), matching the landing's
 * neo-brutalist paper theme: cream #f3e8c9, ink #1a1a1a, accent green #0f9d63.
 */

const INK = "#1a1a1a";
const CREAM = "#f3e8c9";
const PAPER = "#fffbe9";
const ACCENT = "#0f9d63";
const ACCENT_SOFT = "#ffe08a";
const MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace";

// Each registrant is "charged" with a randomly assigned developer crime.
const CHARGES = [
  "excessive faith in AI-generated code",
  "shipping to production on a Friday afternoon",
  "reading the ticket only after opening the PR",
  'committing with the message "fixed it"',
  "merging without reading the diff",
  "trusting the linter to catch everything",
  'declaring a 40-file refactor a "quick fix"',
  "leaving a TODO that is now three years old",
  'saying "it works on my machine" under oath',
  "approving your own PR at 2am",
];

function pick<T>(list: T[], seed: string): T {
  // Deterministic per-email so a given address always gets the same charge.
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) hash = (hash * 31 + seed.charCodeAt(i)) | 0;
  return list[Math.abs(hash) % list.length];
}

export function buildWaitlistEmail(email: string): { subject: string; html: string; text: string } {
  const charge = pick(CHARGES, email);
  const caseNo = `TRB-${(Math.abs([...email].reduce((a, c) => a * 33 + c.charCodeAt(0), 7)) % 9000) + 1000}`;
  const subject = "⚖️ You've been summoned — Code Tribunal";

  const text = [
    "HEAR YE, HEAR YE.",
    "",
    `Case ${caseNo}: the Code Tribunal acknowledges your petition for early access.`,
    `You stand charged with ${charge}.`,
    "Good news: the court is still in recess. Sentencing (a.k.a. your invite) arrives the day we open.",
    "",
    "Your standing trust score: 100/100. Don't push to main.",
    "",
    "— The Clerk of the Court, Code Tribunal",
  ].join("\n");

  const html = `<!doctype html>
<html>
<body style="margin:0;padding:0;background:${CREAM};">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">Case ${caseNo} filed. You're on the docket.</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${CREAM};padding:28px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:${PAPER};border:3px solid ${INK};border-radius:14px;box-shadow:6px 6px 0 ${INK};">
        <tr><td style="padding:26px 28px 8px 28px;">
          <div style="font-family:${MONO};font-size:12px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:${INK};">CODE_TRIBUNAL<span style="color:${ACCENT};">_</span></div>
          <div style="font-family:${MONO};font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#55504a;margin-top:4px;">Case ${caseNo} &middot; Summons</div>
        </td></tr>
        <tr><td style="padding:6px 28px 0 28px;">
          <h1 style="margin:12px 0 0 0;font-family:Georgia,'Times New Roman',serif;font-size:30px;line-height:1.15;color:${INK};">Hear ye, hear ye.</h1>
          <p style="margin:14px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#33302b;">
            The Code Tribunal acknowledges your petition for early access. Your seat in the gallery is reserved.
          </p>
        </td></tr>
        <tr><td style="padding:18px 28px 0 28px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:2px solid ${INK};border-radius:10px;border-left:7px solid ${ACCENT};background:${CREAM};">
            <tr><td style="padding:14px 16px;">
              <div style="font-family:${MONO};font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#55504a;">The charge</div>
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:16px;font-weight:700;color:${INK};margin-top:6px;">You stand charged with ${charge}.</div>
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#55504a;margin-top:8px;line-height:1.55;">
                Plea: irrelevant. The court reads the ticket, cross-examines the diff, and rules regardless.
              </div>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:18px 28px 0 28px;">
          <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#33302b;">
            Good news: the court is in recess. Your sentencing — an invitation to the hosted court — is delivered the day we open. Until then, seven AI agents are warming up to judge your pull requests.
          </p>
        </td></tr>
        <tr><td align="center" style="padding:22px 28px 6px 28px;">
          <table role="presentation" cellpadding="0" cellspacing="0" style="border:3px double ${ACCENT};border-radius:999px;">
            <tr><td align="center" style="padding:16px 22px;">
              <div style="font-family:${MONO};font-size:9px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:${ACCENT};">Tribunal</div>
              <div style="font-family:${MONO};font-size:15px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:${ACCENT};">On the docket</div>
              <div style="font-family:${MONO};font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:${ACCENT};margin-top:3px;">Trust score 100/100</div>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:14px 28px 26px 28px;">
          <div style="border-top:2px dotted ${INK};padding-top:14px;font-family:${MONO};font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#55504a;">
            — The Clerk of the Court
          </div>
          <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#8f8975;margin-top:8px;line-height:1.5;">
            You're receiving this because you requested early access at code-tribunal. Don't push to main.
          </div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;

  return { subject, html, text };
}
