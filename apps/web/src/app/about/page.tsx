import Link from "next/link";

export const metadata = {
  title: "About · Code Council",
  description: "Why Code Council exists and how it differs from PR-bot tools.",
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
          Code Council Tribunal
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-fg-muted">
          Multi-model analysis in the browser. Band-coordinated intent review in your coding agent.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">What this is</h2>
        <p className="text-sm leading-relaxed text-fg">
          Code Council is a multi-model code analysis sandbox. Instead of one AI verdict, it streams several
          frontier model opinions over the same code in parallel and shows where they agree, disagree, or miss
          things entirely.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Why this exists</h2>
        <p className="text-sm leading-relaxed text-fg">
          Most code-review AI products optimize for a single fast answer at PR time. That is useful, but it
          hides one of the most interesting parts of working with models: they often notice different risks,
          emphasize different tradeoffs, and disagree in ways that are actually informative.
        </p>
        <p className="text-sm leading-relaxed text-fg">
          Code Council turns that disagreement into the product. The point is not to auto-merge fixes or
          replace engineering judgment — it is to give you a place to inspect how four frontier models think
          about the same snippet, with streamed output, consensus signals, static scans, and multimodal input.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Tribunal</h2>
        <p className="text-sm leading-relaxed text-fg">
          Tribunal puts AI-generated diffs on trial: Band-coordinated agents compare the ticket against the
          implementation, catch omissions and scope drift, and issue a merge verdict with a traceability ledger.
          It runs in the browser as a demo and ships as a CLI and MCP server you can wire into Claude Code,
          Codex, or Cursor to gate real pull requests.
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
