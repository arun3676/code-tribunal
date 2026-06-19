"use client";

import Link from "next/link";
import type { Route } from "next";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";

import { getHealth, getModels, type ModelInfo } from "@/lib/api";

export function AppShell({ children }: PropsWithChildren) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [online, setOnline] = useState(true);

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

  const availability = useMemo(() => models.filter((model) => model.available), [models]);

  return (
    <div className="flex h-screen flex-col overflow-hidden text-fg">
      <header className="shrink-0 z-20 border-b-[2.5px] border-[color:var(--ink)] bg-[color:var(--bg-overlay)]">
        <div className="flex h-12 w-full items-center justify-between px-5">
          <div className="flex items-center gap-3">
            <Link href="/" className="font-mono text-sm font-bold tracking-[0.24em] text-fg">
              CODE_COUNCIL<span className="animate-pulse">_</span>
            </Link>
            <Link
              href={"/tribunal" as Route}
              className="btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--arbiter)] px-2.5 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
            >
              Tribunal
            </Link>
          </div>
          <div className="flex items-center gap-2">
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
        </div>
      </header>
      <main className="min-h-0 flex-1 overflow-hidden px-4 py-3">{children}</main>
    </div>
  );
}
