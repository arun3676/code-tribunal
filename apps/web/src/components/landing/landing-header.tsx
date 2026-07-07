"use client";

import Link from "next/link";

/**
 * Sticky landing top bar — cream overlay with a hard ink bottom border.
 * Mobile keeps it minimal: wordmark + Demo CTA only.
 */

import { GITHUB_URL } from "@/lib/site";

export function LandingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)]/90 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        <Link href="/" className="min-w-0 font-mono text-sm font-bold tracking-[0.14em] text-fg" aria-label="Code Tribunal home">
          <span className="truncate">CODE_TRIBUNAL</span>
          <span className="animate-pulse" aria-hidden="true">
            _
          </span>
        </Link>

        <nav aria-label="Landing" className="flex shrink-0 items-center gap-4">
          <Link href="/council" className="hidden font-mono text-xs font-bold uppercase tracking-[0.16em] text-fg-muted hover:text-fg sm:inline">
            Council
          </Link>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden font-mono text-xs font-bold uppercase tracking-[0.16em] text-fg-muted hover:text-fg sm:inline"
          >
            GitHub
          </a>
          <Link
            href="/tribunal"
            className="btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--accent-soft)] px-3 py-1.5 font-mono text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--ink)]"
          >
            Demo
          </Link>
        </nav>
      </div>
    </header>
  );
}
