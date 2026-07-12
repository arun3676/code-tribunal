import Link from "next/link";

export const metadata = {
  title: "About",
  description: "Why Code Tribunal exists and how it differs from PR-bot tools.",
};

export default function AboutPage() {
  return (
    /*
     * Use <article> not <main> — AppShell already provides the <main> landmark.
     * Nested <main> elements are invalid HTML and break screen-reader navigation.
     * Outer <main> provides pb-24 on mobile to clear the fixed bottom nav.
     */
    <article className="mx-auto max-w-3xl space-y-8 px-4 py-8 sm:py-10">
      <header>
        {/* Back link: inline-flex + min-h ensures ≥40px tap target on mobile */}
        <Link
          href="/"
          className="inline-flex items-center min-h-[40px] font-mono text-xs uppercase tracking-[0.2em] text-fg-muted hover:text-accent"
        >
          ← back
        </Link>
        <h1 className="mt-2 font-mono text-xl sm:text-2xl uppercase tracking-[0.16em] text-accent">
          Code Tribunal
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-fg-muted">
          An intent-conformance court for AI-generated code — in the browser, in your CI, and in your coding agent.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">What this is</h2>
        <p className="text-sm leading-relaxed text-fg">
          Tribunal puts AI-generated diffs on trial: seven coordinated agents compare the ticket against the
          implementation, catch omissions and scope drift, and issue a merge verdict with a 0–100 trust score
          and a traceability ledger. It runs in the browser as the <Link href="/tribunal" className="underline underline-offset-2 text-fg">War Room</Link>,
          and ships as a CLI and MCP server you can wire into Claude Code, Codex, or Cursor to gate real pull
          requests.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Why this exists</h2>
        <p className="text-sm leading-relaxed text-fg">
          Linters check style. Tests check behavior. Nothing checks whether the diff actually does what the
          ticket asked — and that is exactly where AI-written code fails: it produces plausible, working code
          that silently skips a requirement, or changes something nobody authorized. Tribunal holds the ticket
          and the diff side by side and prices the difference. The verdict is deterministic arithmetic over
          agent-gathered evidence, so the same diff always gets the same answer.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Code Council</h2>
        <p className="text-sm leading-relaxed text-fg">
          The <Link href="/council" className="underline underline-offset-2 text-fg">Council editor</Link> is the
          companion sandbox: instead of one AI verdict, it streams several frontier model opinions over the same
          code in parallel and shows where they agree, disagree, or miss things entirely — with consensus
          signals, static scans, and multimodal input.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Stack</h2>
        <ul className="grid gap-1.5 text-sm text-fg-muted sm:grid-cols-2">
          <li>· Next.js 15 + Tailwind</li>
          <li>· FastAPI + SSE streaming</li>
          <li>· CLI + MCP server (uvx)</li>
          <li>· Groq, Cerebras, Gemini · coordinated over Band</li>
        </ul>
      </section>

      <footer className="border-t-2 border-[color:var(--ink)] pt-4">
        {/* Inline-flex + min-h ensures ≥40px tap target on mobile */}
        <a
          href="https://github.com/arun3676/code-tribunal"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center min-h-[40px] font-mono text-xs uppercase tracking-[0.2em] text-fg-muted hover:text-accent"
        >
          source on github →
        </a>
      </footer>
    </article>
  );
}
