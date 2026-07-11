"use client";

import type { Verdict } from "@/lib/api";

const STATE_META: Record<Verdict["state"], { label: string; color: string }> = {
  CONFORMS: { label: "CONFORMS", color: "var(--accent)" },
  CONFORMS_WITH_CONDITIONS: { label: "WITH CONDITIONS", color: "var(--warning)" },
  DOES_NOT_CONFORM: { label: "DOES NOT CONFORM", color: "var(--danger)" },
};

export function VerdictStamp({ state, merge }: { state: Verdict["state"]; merge: Verdict["merge_decision"] }) {
  const meta = STATE_META[state];
  return (
    <div className="flex items-center justify-center overflow-hidden py-3">
      <div
        className="stamp-press relative flex h-28 w-28 flex-col items-center justify-center rounded-full text-center sm:h-36 sm:w-36"
        style={{
          border: `4px double ${meta.color}`,
          color: meta.color,
          background: `color-mix(in srgb, ${meta.color} 12%, #ffffff)`,
          boxShadow: `0 0 0 2px ${meta.color}`,
        }}
      >
        <div className="absolute inset-1.5 rounded-full border-2" style={{ borderColor: `color-mix(in srgb, ${meta.color} 55%, transparent)` }} />
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.25em] opacity-80">Tribunal</span>
        <span className="mt-1 max-w-[6rem] px-1 font-mono text-[12px] font-bold leading-tight sm:max-w-[7rem] sm:text-[13px]">{meta.label}</span>
        <span className="mt-1.5 rounded-sm border-2 px-1.5 py-0.5 font-mono text-[10px] font-bold tracking-widest" style={{ borderColor: meta.color }}>
          {merge}
        </span>
      </div>
    </div>
  );
}
