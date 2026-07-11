"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "next";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";
import { Home, LayoutGrid, Scale, Info } from "lucide-react";

import { getHealth, getModels, type ModelInfo } from "@/lib/api";

const NAV_TABS = [
  { href: "/", label: "Home", Icon: Home },
  { href: "/council", label: "Council", Icon: LayoutGrid },
  { href: "/tribunal", label: "Tribunal", Icon: Scale },
  { href: "/about", label: "About", Icon: Info },
] as const;

export function AppShell({ children }: PropsWithChildren) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [online, setOnline] = useState(true);
  const [status, setStatus] = useState("");
  const pathname = usePathname();

  useEffect(() => {
    getModels().then(setModels).catch(() => setModels([]));
    const checkHealth = () => {
      getHealth()
        .then(() => setOnline(true))
        .catch(() => setOnline(false));
    };
    checkHealth();
    const interval = window.setInterval(checkHealth, 5000);
    return () => window.clearInterval(interval);
  }, []);

  // Council page broadcasts run progress ("council: 2/4 responding") here.
  useEffect(() => {
    const onStatus = (event: Event) => setStatus(String((event as CustomEvent).detail ?? ""));
    window.addEventListener("code-council-status", onStatus);
    return () => window.removeEventListener("code-council-status", onStatus);
  }, []);

  const availability = useMemo(() => models.filter((model) => model.available), [models]);

  return (
    <div className="flex min-h-[100dvh] flex-col text-fg md:h-screen md:overflow-hidden">
      <header className="shrink-0 z-20 border-b-[2.5px] border-[color:var(--ink)] bg-[color:var(--bg-overlay)]">
        <div className="flex h-12 w-full items-center justify-between px-4 md:px-5">
          <div className="flex items-center gap-3">
            <Link href="/" className="font-mono text-sm font-bold tracking-[0.24em] text-fg">
              CODE_TRIBUNAL<span className="animate-pulse">_</span>
            </Link>
            <Link
              href={"/council" as Route}
              className="hidden sm:inline-block btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--clerk)] px-2.5 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
            >
              Council
            </Link>
            <Link
              href={"/tribunal" as Route}
              className="btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--arbiter)] px-2.5 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
            >
              Tribunal
            </Link>
          </div>
          <div className="flex items-center gap-2">
            {/* Desktop: live run status from the council page */}
            {status ? (
              <span className="hidden md:inline max-w-[220px] truncate font-mono text-[10px] uppercase tracking-[0.12em] text-fg-muted">
                {status}
              </span>
            ) : null}
            {/* Desktop: per-model availability dots */}
            <div className="hidden md:flex items-center gap-2">
              {models.map((model) => (
                <div
                  key={model.id}
                  title={model.display}
                  className="h-3 w-3 rounded-full border-2 border-[color:var(--ink)]"
                  style={{ backgroundColor: model.available ? model.color : "transparent" }}
                />
              ))}
              {availability.length === 0 && !online ? (
                <span className="font-mono text-[11px] font-bold text-danger">OFFLINE</span>
              ) : null}
            </div>
            {/* Mobile: compact "N online" pill — min 11px per rubric */}
            <div className="flex md:hidden items-center">
              {!online ? (
                <span className="font-mono text-[11px] font-bold text-danger">OFFLINE</span>
              ) : (
                <span className="rounded-full border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-2 py-0.5 font-mono text-[11px] font-bold text-fg">
                  {availability.length} online
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/*
       * pb-24 on mobile clears the fixed bottom-nav (h-14=56px + safe-area).
       * md:pb-3 restores normal desktop bottom padding.
       * pt-3 is explicit so py-3 intent is clear (pb-24 overrides pb-3 on mobile).
       */}
      <main className="min-h-0 flex-1 px-4 pt-3 pb-24 md:overflow-hidden md:pb-3">{children}</main>

      {/* Mobile bottom-tab nav — hidden on md+ */}
      <nav
        aria-label="Main navigation"
        className="md:hidden fixed inset-x-0 bottom-0 z-30 border-t-[2.5px] border-[color:var(--ink)] bg-[color:var(--bg-overlay)]"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        {/*
         * h-14 (56px) is the tap-row height above safe-area inset.
         * Each Link fills the full height via items-stretch + self-stretch,
         * guaranteeing ≥44px tap target even on notched devices.
         */}
        <div className="flex h-14 items-stretch">
          {NAV_TABS.map(({ href, label, Icon }) => {
            const isActive =
              href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href as Route}
                aria-current={isActive ? "page" : undefined}
                className={[
                  "flex flex-1 flex-col items-center justify-center gap-0.5",
                  "font-mono text-[11px] font-bold uppercase tracking-[0.12em]",
                  "transition-colors",
                  // Active tab: accent text + subtle accent-soft background slab for contrast
                  isActive
                    ? "text-[color:var(--accent)] bg-[color:var(--accent-soft)]/40"
                    : "text-fg-muted",
                ].join(" ")}
              >
                <Icon
                  size={20}
                  strokeWidth={isActive ? 2.5 : 1.75}
                  aria-hidden="true"
                />
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
