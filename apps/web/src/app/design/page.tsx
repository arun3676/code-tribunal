const colors = [
  ["bg", "var(--bg)"],
  ["bg-elevated", "var(--bg-elevated)"],
  ["bg-overlay", "var(--bg-overlay)"],
  ["border", "var(--border)"],
  ["border-hot", "var(--border-hot)"],
  ["fg", "var(--fg)"],
  ["fg-muted", "var(--fg-muted)"],
  ["fg-dim", "var(--fg-dim)"],
  ["accent", "var(--accent)"],
  ["danger", "var(--danger)"],
  ["warning", "var(--warning)"],
  ["info", "var(--info)"],
] as const;

export default function DesignPage() {
  return (
    <div className="space-y-6">
      <section className="panel rounded-2xl p-6">
        <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-fg-muted">Design System</p>
        <h1 className="mt-2 text-3xl font-semibold text-fg">Refined Matrix</h1>
        <p className="mt-2 max-w-3xl text-sm text-fg-muted">
          Compact density, softened phosphor body text, saturated green only on active states.
        </p>
      </section>
      <section className="grid gap-4 md:grid-cols-3">
        {colors.map(([name, value]) => (
          <div key={name} className="panel rounded-xl p-4">
            <div className="h-16 rounded-lg border border-[color:var(--border)]" style={{ background: value }} />
            <div className="mt-3 font-mono text-xs uppercase tracking-[0.18em] text-fg-muted">{name}</div>
            <div className="mt-1 text-sm text-fg">{value}</div>
          </div>
        ))}
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="panel rounded-xl p-5">
          <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-fg-muted">Typography</div>
          <h2 className="mt-3 text-2xl font-semibold">Heading Scale</h2>
          <p className="mt-2 text-sm text-fg-muted">Body text defaults to 14px for tighter density than the legacy UI.</p>
          <div className="mt-4 space-y-2">
            <div className="text-lg font-semibold">Geist Sans heading</div>
            <div className="text-sm">Geist Sans body text</div>
            <div className="font-mono text-sm">JetBrains Mono telemetry / model IDs / metrics</div>
          </div>
        </div>
        <div className="panel rounded-xl p-5">
          <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-fg-muted">Primitives</div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button className="rounded-lg border border-[color:var(--border-hot)] bg-[color:var(--accent-soft)] px-4 py-2 text-sm text-fg">Accent Button</button>
            <button className="rounded-lg border border-[color:var(--border)] px-4 py-2 text-sm text-fg-muted">Secondary</button>
            <span className="rounded-full border border-[color:var(--border-hot)] px-3 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-accent">Badge</span>
          </div>
          <div className="mt-4 rounded-xl border border-[color:var(--border)] bg-[rgba(5,8,5,0.9)] p-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Panel</div>
            <div className="mt-2 text-sm text-fg">Chrome, borders, and spacing reference.</div>
          </div>
        </div>
      </section>
    </div>
  );
}
