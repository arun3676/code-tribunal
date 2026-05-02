"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import type { Route } from "next";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";

import { getHealth, getModels, type ModelInfo } from "@/lib/api";

const MatrixRain = dynamic(() => import("@/components/effects/matrix-rain").then((mod) => mod.MatrixRain), { ssr: false });

export function AppShell({ children }: PropsWithChildren) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [status, setStatus] = useState("ready");
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
    const onStatus = (event: Event) => {
      const custom = event as CustomEvent<string>;
      if (custom.detail) {
        setStatus(custom.detail);
      }
    };
    window.addEventListener("code-council-status", onStatus as EventListener);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("code-council-status", onStatus as EventListener);
    };
  }, []);

  const availability = useMemo(() => models.filter((model) => model.available), [models]);

  return (
    <div className="min-h-screen bg-bg text-fg">
      <MatrixRain />
      <header className="sticky top-0 z-20 border-b border-[color:var(--border)] bg-[rgba(5,8,5,0.82)] backdrop-blur">
        <div className="mx-auto flex h-12 max-w-7xl items-center justify-between px-2 sm:px-4">
          <Link href="/" className="font-mono text-xs tracking-[0.18em] text-fg sm:text-sm sm:tracking-[0.24em]">
            CODE_COUNCIL<span className="animate-pulse text-accent">_</span>
          </Link>
          <div className="flex items-center gap-2">
            {models.map((model) => (
              <div key={model.id} title={model.display} className="h-2.5 w-2.5 rounded-full border border-black/20" style={{ backgroundColor: model.available ? model.color : "#253128" }} />
            ))}
            {availability.length === 0 ? <span className="font-mono text-[11px] text-danger">BACKEND_OFFLINE</span> : null}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 pb-16 pt-5">{children}</main>
      <div className="fixed bottom-0 left-0 right-0 z-20 flex items-center justify-between gap-3 border-t border-[color:var(--border)] bg-[rgba(10,15,10,0.92)] px-2 py-2 font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted sm:px-4">
        <span className="truncate">{online ? status : "BACKEND_OFFLINE"}</span>
        <Link href={"/about" as Route} className="shrink-0 text-fg-muted hover:text-accent">about</Link>
      </div>
    </div>
  );
}
