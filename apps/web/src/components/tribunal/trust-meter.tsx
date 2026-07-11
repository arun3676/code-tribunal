"use client";

type Props = { score: number };

function scoreColor(score: number): string {
  if (score <= 49) return "var(--danger)";
  if (score <= 79) return "var(--warning)";
  return "var(--accent)";
}

export function TrustMeter({ score }: Props) {
  const color = scoreColor(score);
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-fg-muted">Trust score</span>
        <span className="font-mono text-2xl font-bold tabular-nums" style={{ color }}>
          {pct}
          <span className="text-sm text-fg-dim">/100</span>
        </span>
      </div>
      <div className="relative h-4 overflow-hidden rounded-full border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)]">
        <div className="absolute inset-y-0 left-1/2 z-10 w-0.5 bg-[color:var(--ink)] opacity-30" />
        <div className="absolute inset-y-0 left-[80%] z-10 w-0.5 bg-[color:var(--ink)] opacity-30" />
        <div
          className="meter-fill h-full"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, var(--danger), var(--warning) 55%, var(--accent))` }}
        />
        {/* needle */}
        <div className="absolute top-1/2 z-20 h-5 w-1 -translate-y-1/2 rounded-sm border border-[color:var(--ink)]" style={{ left: `calc(${pct}% - 2px)`, background: color }} />
      </div>
      <div className="mt-1 flex justify-between font-mono text-[10px] font-bold uppercase tracking-wider text-fg-dim">
        <span>Block</span>
        <span>Conditions</span>
        <span>Clear</span>
      </div>
    </div>
  );
}
