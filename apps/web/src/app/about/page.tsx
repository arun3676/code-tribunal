import Link from "next/link";

export const metadata = {
  title: "About · Code Council",
  description: "Why Code Council exists and how it differs from PR-bot tools.",
};

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-3xl space-y-8 px-4 py-10">
      <header>
        <Link href="/" className="font-mono text-xs uppercase tracking-[0.2em] text-fg-muted hover:text-accent">
          ← back
        </Link>
        <h1 className="mt-4 font-mono text-2xl uppercase tracking-[0.16em] text-accent">Code Council</h1>
        <p className="mt-2 text-sm text-fg-muted">See how frontier models reason about your code.</p>
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
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Stack</h2>
        <ul className="grid gap-1 text-sm text-fg-muted sm:grid-cols-2">
          <li>· Next.js 15 + Tailwind</li>
          <li>· FastAPI + SSE streaming</li>
          <li>· Vercel + Railway</li>
          <li>· Gemini, DeepSeek, Mercury, Kimi</li>
        </ul>
      </section>

      <footer className="border-t border-[color:var(--border)] pt-4">
        <a
          href="https://github.com/arun3676/llm-code-analyzer"
          className="font-mono text-xs uppercase tracking-[0.2em] text-fg-muted hover:text-accent"
        >
          source on github →
        </a>
      </footer>
    </main>
  );
}
