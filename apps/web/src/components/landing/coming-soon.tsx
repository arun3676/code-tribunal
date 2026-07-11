import Link from "next/link";

/**
 * Coming-soon gate for the live product surfaces (/council, /tribunal) while
 * the backend is not yet deployed. To reveal the real pages, set
 * NEXT_PUBLIC_DEMO_ENABLED="true" in the Vercel env AND redeploy — NEXT_PUBLIC_
 * values are inlined at build time, so an env flip alone changes nothing.
 */
export function ComingSoon({ title, blurb }: { title: string; blurb: string }) {
  return (
    <main className="mx-auto flex min-h-[70vh] max-w-2xl flex-col items-center justify-center gap-5 px-4 text-center">
      <div className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-fg-muted">
        Coming Soon
      </div>
      <h1 className="text-3xl font-bold leading-tight sm:text-4xl">{title}</h1>
      <p className="max-w-xl text-fg-muted">{blurb}</p>
      <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/#waitlist"
          className="btn-tactile rounded-xl border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-6 py-3 font-mono text-sm font-bold uppercase tracking-[0.16em] text-[color:var(--ink)]"
        >
          Get early access →
        </Link>
        <Link
          href="/"
          className="font-mono text-xs font-bold uppercase tracking-[0.16em] text-fg-muted hover:text-fg"
        >
          ← Back to home
        </Link>
      </div>
    </main>
  );
}

/** Whether the live product surfaces are enabled (backend deployed). */
export const DEMO_ENABLED = process.env.NEXT_PUBLIC_DEMO_ENABLED === "true";
