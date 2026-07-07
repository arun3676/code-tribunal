"use client";

import Link from "next/link";
import { Reveal } from "@/components/landing/motion-primitives";

/** Ink-top-border landing footer: wordmark, tagline, link columns, microline. */

import { GITHUB_URL } from "@/lib/site";

export function LandingFooter() {
  return (
    <footer className="border-t-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)]">
      <Reveal className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0 max-w-sm">
            <div className="font-mono text-sm font-bold tracking-[0.14em]">
              CODE_TRIBUNAL
              <span className="animate-pulse" aria-hidden="true">
                _
              </span>
            </div>
            <p className="mt-2 text-[13px] leading-snug text-fg-muted">
              Seven courtroom agents cross-examine every diff against its ticket — and rule.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8">
            <nav aria-label="Product">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-fg-dim">Product</div>
              <ul className="mt-3 space-y-2 text-[13px] font-medium">
                <li>
                  <Link href="/tribunal" className="text-fg-muted hover:text-fg">
                    Live demo
                  </Link>
                </li>
                <li>
                  <Link href="/council" className="text-fg-muted hover:text-fg">
                    Code Council
                  </Link>
                </li>
                <li>
                  <Link href="/about" className="text-fg-muted hover:text-fg">
                    About
                  </Link>
                </li>
              </ul>
            </nav>

            <nav aria-label="Install">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-fg-dim">Install</div>
              <ul className="mt-3 space-y-2 text-[13px] font-medium">
                <li>
                  <a href="#install" className="text-fg-muted hover:text-fg">
                    CLI &amp; MCP
                  </a>
                </li>
                <li>
                  <a href="#waitlist" className="text-fg-muted hover:text-fg">
                    Early access
                  </a>
                </li>
                <li>
                  <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="text-fg-muted hover:text-fg">
                    GitHub
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>

        <p className="mt-10 border-t-2 border-dotted border-[color:var(--ink)] pt-4 font-mono text-[10px] uppercase tracking-[0.16em] text-fg-dim">
          MIT · built with free-tier LLMs · Groq / Cerebras / Gemini
        </p>
      </Reveal>
    </footer>
  );
}
