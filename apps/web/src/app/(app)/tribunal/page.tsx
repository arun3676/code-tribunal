"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { ComingSoon, DEMO_ENABLED } from "@/components/landing/coming-soon";

import {
  getTribunalFixtures,
  reviewPr,
  tribunal,
  tribunalVerdict,
  type AgentName,
  type TribunalEvent,
  type TribunalFixture,
  type TribunalVerdictResult,
  type Verdict,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { useFocusTrap } from "@/lib/use-focus-trap";
import { AgentAvatar } from "@/components/tribunal/agent-avatar";
import { AgentCard } from "@/components/tribunal/agent-card";
import { PERSONAS, TRIAL_ORDER } from "@/components/tribunal/personas";
import { TrustMeter } from "@/components/tribunal/trust-meter";
import { VerdictStamp } from "@/components/tribunal/verdict-stamp";
import { EvidenceTagIcon, GavelIcon, ScalesIcon, SealIcon } from "@/components/tribunal/justice-icons";

const MonacoEditor = dynamic(async () => (await import("@monaco-editor/react")).default, {
  ssr: false,
  loading: () => <div className="flex h-[200px] items-center justify-center rounded-xl border border-border text-xs text-dim">Loading diff…</div>,
});

type Chip = {
  id: string;
  label: string;
  detail: string;
  severity: "critical" | "high" | "medium" | "low" | "neutral";
  fileRef?: string;
};

type Turn = {
  id: number;
  kind: "message" | "recruitment";
  agent: AgentName;
  text: string;
  target?: AgentName[] | null;
  chips: Chip[];
};

const SEVERITY_COLOR: Record<Chip["severity"], string> = {
  critical: "var(--danger)",
  high: "var(--danger)",
  medium: "var(--warning)",
  low: "var(--info)",
  neutral: "var(--fg-dim)",
};

function eventToChip(ev: TribunalEvent, seq: number): Chip | null {
  const kind = ev.payload?.kind as string | undefined;
  if (kind === "requirement") {
    const r = ev.payload.requirement;
    return { id: `c${seq}`, label: `${r.id} · ${r.priority?.toUpperCase?.() ?? "MUST"}`, detail: r.text, severity: "neutral" };
  }
  if (kind === "implementation") {
    const f = ev.payload.finding;
    return { id: `c${seq}`, label: f.id, detail: f.summary, severity: "low", fileRef: f.file_ref };
  }
  if (kind === "omission" || kind === "scope_drift" || kind === "constraint") {
    const f = ev.payload.finding;
    return {
      id: `c${seq}`,
      label: kind === "omission" ? `MISSING · ${f.requirement_id ?? ""}` : kind === "scope_drift" ? "UNAUTHORIZED" : "POLICY",
      detail: f.detail,
      severity: (f.severity as Chip["severity"]) ?? "high",
      fileRef: f.file_ref ?? undefined,
    };
  }
  return null;
}

export default function TribunalPage() {
  if (!DEMO_ENABLED) {
    return (
      <ComingSoon
        title="The Tribunal War Room is coming soon"
        blurb="Watch seven AI agents cross-examine a real diff against its ticket and stamp a merge verdict. It ships alongside the hosted court."
      />
    );
  }
  return <TribunalApp />;
}

function TribunalApp() {
  const [fixtures, setFixtures] = useState<TribunalFixture[]>([]);
  const [fixtureId, setFixtureId] = useState<string>("");
  const [ticket, setTicket] = useState("");
  const [diff, setDiff] = useState("");
  const [domains, setDomains] = useState<string[]>([]);

  const [running, setRunning] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [spoken, setSpoken] = useState<Set<AgentName>>(new Set());
  const [current, setCurrent] = useState<AgentName | null>(null);
  const [roster, setRoster] = useState<AgentName[]>(TRIAL_ORDER.filter((a) => a !== "WARDEN"));
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [bandMode, setBandMode] = useState<"live" | "demo">("demo");
  const [error, setError] = useState<string | null>(null);
  const [rulingExpanded, setRulingExpanded] = useState(false);
  const rulingDialogRef = useFocusTrap<HTMLDivElement>(rulingExpanded && verdict !== null);

  // Mobile-only flow controls (desktop chamber ignores these).
  const [mobileMode, setMobileMode] = useState<"case" | "paste" | "pr">("case");
  const [quickVerdict, setQuickVerdict] = useState(false);
  const [prUrl, setPrUrl] = useState("");
  const [shareCopied, setShareCopied] = useState(false);

  const seq = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const streamRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    getTribunalFixtures()
      .then((list) => {
        setFixtures(list);
        if (list[0]) selectFixture(list[0]);
      })
      .catch(() => setFixtures([]));
    return () => abortRef.current?.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    streamRef.current?.scrollTo({ top: streamRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  useEffect(() => {
    if (!rulingExpanded) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setRulingExpanded(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [rulingExpanded]);

  function selectFixture(fx: TribunalFixture) {
    setFixtureId(fx.id);
    setTicket(fx.ticket.trim());
    setDiff(fx.diff.trim());
    setDomains(fx.touched_domains ?? []);
  }

  function reset() {
    abortRef.current?.abort();
    setRunning(false);
    setTurns([]);
    setSpoken(new Set());
    setCurrent(null);
    setVerdict(null);
    setError(null);
    setRoster(TRIAL_ORDER.filter((a) => a !== "WARDEN"));
  }

  function markSpoken(agent: AgentName) {
    setSpoken((prev) => new Set(prev).add(agent));
    setCurrent(agent);
  }

  function pushTurn(turn: Omit<Turn, "id">) {
    seq.current += 1;
    setTurns((prev) => [...prev, { ...turn, id: seq.current }]);
  }

  function attachChip(agent: AgentName, chip: Chip) {
    setTurns((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.agent === agent && last.kind === "message") {
        next[next.length - 1] = { ...last, chips: [...last.chips, chip] };
        return next;
      }
      seq.current += 1;
      next.push({ id: seq.current, kind: "message", agent, text: "", chips: [chip] });
      return next;
    });
  }

  async function convene() {
    if (running) return;
    reset();
    setRunning(true);
    const controller = new AbortController();
    abortRef.current = controller;
    const payload = fixtureId
      ? { fixture_id: fixtureId }
      : { ticket, diff, touched_domains: domains, title: "Ad-hoc tribunal" };

    try {
      for await (const ev of tribunal(payload, controller.signal)) {
        handleEvent(ev);
      }
    } catch (err) {
      if (!controller.signal.aborted) setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
      setCurrent(null);
    }
  }

  /** Replay a one-shot result's transcript through the same renderer the SSE path uses. */
  function applyResult(result: TribunalVerdictResult) {
    for (const ev of result.transcript ?? []) {
      handleEvent(ev);
    }
    setBandMode(result.band_mode ?? "demo");
    setVerdict(result.verdict);
    markSpoken("ARBITER");
  }

  /** One-shot verdict (no SSE) — used for Paste + "Quick verdict" on mobile. */
  async function conveneQuick() {
    if (running) return;
    reset();
    setRunning(true);
    const payload = fixtureId
      ? { fixture_id: fixtureId }
      : { ticket, diff, touched_domains: domains, title: "Ad-hoc tribunal" };
    try {
      applyResult(await tribunalVerdict(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
      setCurrent(null);
    }
  }

  /** PR URL → one-shot verdict. */
  async function conveneFromPr() {
    if (running || !prUrl.trim()) return;
    reset();
    setRunning(true);
    try {
      applyResult(await reviewPr(prUrl.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
      setCurrent(null);
    }
  }

  /** Mobile "Run" — routes to the right path based on the selected mode. */
  function runMobile() {
    if (mobileMode === "pr") return conveneFromPr();
    if (mobileMode === "paste" && quickVerdict) return conveneQuick();
    return convene();
  }

  async function shareVerdict() {
    if (!verdict) return;
    const summary =
      `Code Tribunal verdict: ${verdict.state} · ${verdict.merge_decision}\n` +
      `Trust score: ${verdict.trust_score}/100\n` +
      `${verdict.summary}`;
    const data = { title: "Code Tribunal verdict", text: summary };
    try {
      if (typeof navigator !== "undefined" && navigator.share) {
        await navigator.share(data);
        return;
      }
    } catch {
      // user dismissed or share failed — fall through to clipboard
    }
    try {
      await navigator.clipboard?.writeText(summary);
      setShareCopied(true);
      window.setTimeout(() => setShareCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  }

  function handleEvent(ev: TribunalEvent) {
    switch (ev.type) {
      case "phase": {
        const agents = (ev.payload.agents as Array<{ name: AgentName }>) ?? [];
        if (agents.length) setRoster(agents.map((a) => a.name));
        setBandMode((ev.payload.band_mode as "live" | "demo") ?? "demo");
        break;
      }
      case "message":
        if (ev.agent) {
          markSpoken(ev.agent);
          pushTurn({ kind: "message", agent: ev.agent, text: ev.text, target: ev.target, chips: [] });
        }
        break;
      case "event": {
        const chip = eventToChip(ev, (seq.current += 1));
        if (chip && ev.agent) {
          markSpoken(ev.agent);
          attachChip(ev.agent, chip);
        }
        break;
      }
      case "recruitment":
        setRoster((prev) => (prev.includes("WARDEN") ? prev : [...prev.slice(0, 5), "WARDEN", ...prev.slice(5)]));
        markSpoken("WARDEN");
        pushTurn({ kind: "recruitment", agent: "WARDEN", text: ev.text, chips: [] });
        break;
      case "verdict":
        markSpoken("ARBITER");
        setVerdict(ev.payload as Verdict);
        break;
      case "done":
        setBandMode((ev.payload.band_mode as "live" | "demo") ?? bandMode);
        break;
      case "error":
        setError(ev.text || (ev.payload?.message as string) || "Trial failed");
        break;
    }
  }

  const rosterOrdered = useMemo(() => TRIAL_ORDER.filter((a) => roster.includes(a)), [roster]);

  return (
    <div className="flex min-h-full flex-col gap-3 lg:h-full">
      {/* Header */}
      <div className="brutal shrink-0 flex flex-wrap items-center justify-between gap-3 px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border-[2.5px] border-[color:var(--ink)] bg-[color:var(--arbiter)]">
            <ScalesIcon size={20} color="var(--ink)" />
          </span>
          <div className="min-w-0">
            <h1 className="font-mono text-base font-bold tracking-[0.12em] text-fg sm:text-lg sm:tracking-[0.16em]">TRIBUNAL · WAR ROOM</h1>
            <p className="text-xs font-medium text-fg-muted">Did the AI build what you actually asked for?</p>
          </div>
        </div>
        <span
          className="shrink-0 whitespace-nowrap rounded-full border-2 border-[color:var(--ink)] px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[color:var(--ink)]"
          style={{ background: bandMode === "live" ? "var(--surveyor)" : "var(--bg-elevated)" }}
        >
          Band · {bandMode === "live" ? "LIVE" : "DEMO"}
        </span>
      </div>

      {/* Plain-language explainer — compact single row */}
      <HowItWorks />

      {/* ===== MOBILE (< lg): vertical run → watch → verdict flow ===== */}
      <MobileTribunal
        fixtures={fixtures}
        fixtureId={fixtureId}
        selectFixture={selectFixture}
        ticket={ticket}
        setTicket={setTicket}
        diff={diff}
        setDiff={setDiff}
        clearFixture={() => setFixtureId("")}
        domains={domains}
        mode={mobileMode}
        setMode={setMobileMode}
        quickVerdict={quickVerdict}
        setQuickVerdict={setQuickVerdict}
        prUrl={prUrl}
        setPrUrl={setPrUrl}
        running={running}
        run={runMobile}
        reset={reset}
        turns={turns}
        current={current}
        roster={rosterOrdered}
        spoken={spoken}
        verdict={verdict}
        bandMode={bandMode}
        error={error}
        shareVerdict={shareVerdict}
        shareCopied={shareCopied}
      />

      {/* ===== DESKTOP (lg+): the original 3-column chamber, unchanged ===== */}
      <div className="hidden min-h-0 flex-1 gap-3 lg:grid lg:grid-cols-[330px_minmax(0,1fr)_360px]">
        {/* LEFT — Docket */}
        <section className="glass flex min-h-0 flex-col gap-3 overflow-y-auto rounded-2xl p-4">
          <SectionTitle icon={<EvidenceTagIcon size={16} color="var(--advocate)" />} label="Docket" />

          <label className="block">
            <span className="mb-1 block font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Demo case</span>
            <select
              value={fixtureId}
              onChange={(e) => {
                const fx = fixtures.find((f) => f.id === e.target.value);
                if (fx) selectFixture(fx);
                else setFixtureId("");
              }}
              className="w-full rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-3 py-2 text-sm font-semibold"
            >
              {fixtures.map((fx) => (
                <option key={fx.id} value={fx.id}>
                  {fx.title}
                </option>
              ))}
              <option value="">Custom (edit below)</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Intent · ticket</span>
            <textarea
              value={ticket}
              onChange={(e) => {
                setTicket(e.target.value);
                setFixtureId("");
              }}
              rows={5}
              className="w-full resize-y rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-3 py-2 font-mono text-xs leading-relaxed"
            />
          </label>

          <div>
            <span className="mb-1 block font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Diff</span>
            <div className="overflow-hidden rounded-lg border-2 border-[color:var(--ink)]">
              <MonacoEditor
                height="200px"
                theme="vs-dark"
                language="diff"
                value={diff}
                onChange={(v: string | undefined) => {
                  setDiff(v ?? "");
                  setFixtureId("");
                }}
                options={{ minimap: { enabled: false }, fontSize: 11, lineNumbers: "off", scrollBeyondLastLine: false, wordWrap: "on" }}
              />
            </div>
          </div>

          {domains.length ? (
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Domains</span>
              {domains.map((d) => (
                <span
                  key={d}
                  className="rounded-full border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-[color:var(--ink)]"
                  style={{ background: d === "auth" || d === "security" ? "var(--warden)" : "var(--bg-elevated)" }}
                >
                  {d}
                </span>
              ))}
            </div>
          ) : null}

          <div className="flex gap-2 pt-1">
            <button
              onClick={convene}
              disabled={running || !ticket.trim() || !diff.trim()}
              className="btn-tactile flex-1 border-[2.5px] border-[color:var(--ink)] bg-[color:var(--arbiter)] px-3 py-2.5 font-mono text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--ink)] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {running ? "Deliberating…" : "⚖ Convene Tribunal"}
            </button>
            <button
              onClick={reset}
              disabled={running}
              className="btn-tactile border-[2.5px] border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-3 py-2.5 font-mono text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--ink)] disabled:opacity-40"
            >
              Reset
            </button>
          </div>
          {error ? <p className="font-mono text-[11px] text-danger">{error}</p> : null}
        </section>

        {/* CENTER — Deliberation floor */}
        <section className="glass chamber-floor flex min-h-0 flex-col rounded-2xl p-4">
          <SectionTitle icon={<GavelIcon size={16} color="var(--clerk)" />} label="Deliberation" />

          {/* Agent roster lanes */}
          <div className="mb-3 mt-2 border-b-2 border-[color:var(--ink)] pb-3">
            <div className="flex flex-wrap gap-3">
              {rosterOrdered.map((agent) => {
                const has = spoken.has(agent);
                const p = PERSONAS[agent];
                return (
                  <div
                    key={agent}
                    title={`${agent} — ${p.nickname}: ${p.summary}`}
                    className={cn("flex cursor-help flex-col items-center gap-1 transition-opacity", has ? "opacity-100" : "opacity-40")}
                  >
                    <AgentAvatar agent={agent} size={40} active={current === agent} />
                    <span className="font-mono text-[10px] font-bold tracking-wider text-fg">{agent}</span>
                  </div>
                );
              })}
            </div>
            {current ? (
              <div className="lane-in mt-3 flex items-center gap-2 rounded-lg border-2 border-[color:var(--ink)] px-2.5 py-1.5 text-[color:var(--ink)]" style={{ background: `color-mix(in srgb, ${PERSONAS[current].color} 30%, #ffffff)` }}>
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" style={{ background: "var(--ink)" }} />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full border border-[color:var(--ink)]" style={{ background: PERSONAS[current].color }} />
                </span>
                <span className="shrink-0 font-mono text-xs font-bold tracking-wider">
                  {current} · {PERSONAS[current].nickname}
                </span>
                <span className="min-w-0 truncate text-xs font-medium italic opacity-80">{PERSONAS[current].tagline}</span>
              </div>
            ) : null}
          </div>

          {/* Transcript */}
          <div ref={streamRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
            {turns.length === 0 ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-center">
                  <SealIcon size={18} color="var(--ink)" />
                  <div className="text-left">
                    <p className="font-mono text-xs font-bold uppercase tracking-[0.18em] text-fg">Meet the chamber</p>
                    <p className="text-[11px] text-muted">Seven specialists. Hit &ldquo;Convene Tribunal&rdquo; and watch them debate your diff.</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
                  {TRIAL_ORDER.map((agent) => (
                    <AgentCard key={agent} agent={agent} />
                  ))}
                </div>
              </div>
            ) : (
              turns.map((turn) =>
                turn.kind === "recruitment" ? (
                  <div
                    key={turn.id}
                    className="chamber-open rounded-xl border-[2.5px] border-[color:var(--ink)] p-3 text-[color:var(--ink)]"
                    style={{ background: "color-mix(in srgb, var(--warden) 30%, #ffffff)", boxShadow: "var(--shadow-ink-sm)" }}
                  >
                    <div className="flex items-start gap-3">
                      <span className="shrink-0">
                        <AgentAvatar agent="WARDEN" size={48} active />
                      </span>
                      <div className="min-w-0 flex-1">
                        <span className="inline-block rounded border-2 border-[color:var(--ink)] bg-[color:var(--warden)] px-2 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.16em]">⚖ Witness summoned · WARDEN</span>
                        <p className="mt-1.5 break-words text-sm font-medium">{turn.text}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <MessageLane key={turn.id} turn={turn} />
                ),
              )
            )}
          </div>
        </section>

        {/* RIGHT — Ruling */}
        <section className="glass flex min-h-0 flex-col gap-4 overflow-y-auto rounded-2xl p-4">
          <div className="flex items-center justify-between gap-2">
            <SectionTitle icon={<GavelIcon size={16} color="var(--ink)" />} label="Ruling" />
            {verdict ? (
              <button
                onClick={() => setRulingExpanded(true)}
                title="Expand the full ruling"
                aria-label="Expand the full ruling"
                className="btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-[color:var(--ink)]"
              >
                ⤢ Expand
              </button>
            ) : null}
          </div>

          {verdict ? (
            <RulingDetails verdict={verdict} />
          ) : (
            <div className="flex min-h-[160px] flex-col items-center justify-center text-center text-dim">
              <GavelIcon size={32} color="var(--fg-dim)" />
              <p className="mt-2 font-mono text-xs uppercase tracking-[0.18em]">Awaiting the ruling</p>
              <p className="mt-1 text-[11px] text-muted">ARBITER drops the gavel here — trust score, merge call & ledger.</p>
            </div>
          )}

          {/* Install — CLI / MCP */}
          <InstallPanel />

          {/* Agent routing badges */}
          <div className="border-t-2 border-[color:var(--ink)] pt-3">
            <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-fg-muted">Agent routing</p>
            <div className="space-y-1">
              {TRIAL_ORDER.map((agent) => (
                <div key={agent} className="flex items-center justify-between gap-2 text-[10px]">
                  <span className="flex items-center gap-1.5 font-mono font-bold tracking-wider text-fg">
                    <span className="h-2.5 w-2.5 shrink-0 rounded-full border border-[color:var(--ink)]" style={{ background: PERSONAS[agent].color }} />
                    {agent}
                  </span>
                  <span className="font-mono font-semibold uppercase tracking-wider text-fg-muted">{PERSONAS[agent].provider}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {/* Expanded ruling — full-screen modal */}
      {rulingExpanded && verdict ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-[color:var(--ink)]/60 p-4 sm:items-center sm:p-8"
          onClick={() => setRulingExpanded(false)}
        >
          <div
            ref={rulingDialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Tribunal ruling — full record"
            tabIndex={-1}
            className="glass relative my-auto flex max-h-[92vh] w-full max-w-2xl flex-col gap-4 overflow-y-auto rounded-2xl border-2 border-[color:var(--ink)] p-4 sm:p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky -top-4 z-10 -mx-4 -mt-4 flex items-center justify-between gap-2 border-b-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-4 py-3 sm:-top-6 sm:-mx-6 sm:-mt-6 sm:px-6">
              <SectionTitle icon={<GavelIcon size={16} color="var(--ink)" />} label="Ruling — Full Record" />
              <button
                onClick={() => setRulingExpanded(false)}
                title="Close (Esc)"
                className="btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-[color:var(--ink)]"
              >
                ✕ Close
              </button>
            </div>
            <RulingDetails verdict={verdict} expanded />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function RulingDetails({ verdict, expanded = false }: { verdict: Verdict; expanded?: boolean }) {
  return (
    <>
      <VerdictStamp state={verdict.state} merge={verdict.merge_decision} />
      <p className="text-center text-xs text-fg-muted">{verdict.summary}</p>
      <TrustMeter score={verdict.trust_score} />

      {verdict.deductions.length ? (
        <div className="rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] p-3">
          <p className="mb-1.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-fg-muted">Score math</p>
          <div className="space-y-1 font-mono text-[11px]">
            <div className="flex justify-between text-muted">
              <span>Baseline</span>
              <span>100</span>
            </div>
            {verdict.deductions.map((d, i) => (
              <div key={i} className="flex justify-between gap-2 text-danger">
                <span className={cn("min-w-0 pr-2", expanded ? "break-words" : "truncate")}>{d.reason}</span>
                <span className="shrink-0">{d.points}</span>
              </div>
            ))}
            <div className="flex justify-between border-t-2 border-[color:var(--ink)] pt-1 font-bold text-fg">
              <span>Trust</span>
              <span>{verdict.trust_score}</span>
            </div>
          </div>
        </div>
      ) : null}

      {verdict.blockers.length ? <Findings title="Blockers" items={verdict.blockers} color="var(--danger)" /> : null}
      {verdict.conditions.length ? <Findings title="Conditions" items={verdict.conditions} color="var(--warning)" /> : null}

      {verdict.ledger.length ? (
        <div>
          <p className="mb-1.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-fg-muted">Traceability ledger</p>
          {/* Mobile (< md): stacked cards — readable without horizontal scroll. */}
          <div className="space-y-2 md:hidden">
            {verdict.ledger.map((row, i) => (
              <div key={i} className="rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] p-2.5 font-mono text-[10px]">
                <div className="flex items-center justify-between gap-2">
                  <span className="min-w-0 break-words font-bold text-fg">{row.requirement_id}</span>
                  <LedgerBadge decision={row.decision} />
                </div>
                <p className="mt-1 break-words leading-snug text-fg-muted">{row.requirement}</p>
              </div>
            ))}
          </div>
          {/* Tablet/desktop (md+): the wide table — overflow-x guard for safety. */}
          <div className="hidden overflow-x-auto rounded-lg border-2 border-[color:var(--ink)] md:block">
            <table className="w-full text-left font-mono text-[10px]">
              <tbody>
                {verdict.ledger.map((row, i) => (
                  <tr key={i} className="border-b border-[color:var(--ink)] border-opacity-20 last:border-0">
                    <td className="whitespace-nowrap px-2 py-1.5 align-top font-bold text-fg">{row.requirement_id}</td>
                    <td className="break-words px-2 py-1.5 align-top text-fg-muted">{row.requirement}</td>
                    <td className="px-2 py-1.5 align-top">
                      <LedgerBadge decision={row.decision} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {expanded && verdict.ledger.some((row) => row.notes || row.code_refs.length) ? (
        <div>
          <p className="mb-1.5 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-fg-muted">Ledger detail</p>
          <div className="space-y-2">
            {verdict.ledger.map((row, i) => (
              <div key={i} className="rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] p-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="min-w-0 break-words font-mono text-[11px] font-bold text-fg">{row.requirement_id}</span>
                  <LedgerBadge decision={row.decision} />
                </div>
                <p className="mt-1 break-words text-[11px] text-fg-muted">{row.requirement}</p>
                {row.notes ? <p className="mt-1 break-words text-[11px] italic text-muted">{row.notes}</p> : null}
                {row.code_refs.length ? (
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {row.code_refs.map((ref, j) => (
                      <span key={j} className="break-all rounded-sm border border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">
                        {ref}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}

type MobileMode = "case" | "paste" | "pr";

type MobileTribunalProps = {
  fixtures: TribunalFixture[];
  fixtureId: string;
  selectFixture: (fx: TribunalFixture) => void;
  ticket: string;
  setTicket: (v: string) => void;
  diff: string;
  setDiff: (v: string) => void;
  clearFixture: () => void;
  domains: string[];
  mode: MobileMode;
  setMode: (m: MobileMode) => void;
  quickVerdict: boolean;
  setQuickVerdict: (v: boolean) => void;
  prUrl: string;
  setPrUrl: (v: string) => void;
  running: boolean;
  run: () => void;
  reset: () => void;
  turns: Turn[];
  current: AgentName | null;
  roster: AgentName[];
  spoken: Set<AgentName>;
  verdict: Verdict | null;
  bandMode: "live" | "demo";
  error: string | null;
  shareVerdict: () => void;
  shareCopied: boolean;
};

/**
 * Mobile-only control/viewer: a single vertical column with three stages —
 * Start → Deliberation → Verdict. Reuses the in-file MessageLane / EvidenceChip /
 * RulingDetails helpers and the shared tribunal/* components; only the chrome is
 * mobile-tuned. Rendered under `lg:hidden`; the desktop chamber is untouched.
 */
function MobileTribunal(props: MobileTribunalProps) {
  const {
    fixtures, fixtureId, selectFixture, ticket, setTicket, diff, setDiff, clearFixture, domains,
    mode, setMode, quickVerdict, setQuickVerdict, prUrl, setPrUrl,
    running, run, reset, turns, current, roster, spoken, verdict, bandMode, error, shareVerdict, shareCopied,
  } = props;

  // Which stage to emphasise. Stages stay mounted (vertical scroll) but we
  // surface the relevant one based on run state.
  const started = running || turns.length > 0 || verdict !== null;

  const canRun =
    mode === "pr" ? Boolean(prUrl.trim()) : Boolean(ticket.trim() && diff.trim());

  const MODES: { id: MobileMode; label: string }[] = [
    { id: "case", label: "Case" },
    { id: "paste", label: "Paste" },
    { id: "pr", label: "PR URL" },
  ];

  return (
    <div className="flex flex-col gap-3 lg:hidden">
      {/* ── Stage 1 · Start ─────────────────────────────────────────── */}
      <section className="glass rounded-2xl p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <SectionTitle icon={<EvidenceTagIcon size={16} color="var(--advocate)" />} label="Start a case" />
          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-dim">Step 1 of 3</span>
        </div>

        {/* Segmented control */}
        <div className="grid grid-cols-3 gap-1 rounded-xl border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] p-1">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              disabled={running}
              aria-pressed={mode === m.id}
              className={cn(
                "flex min-h-[40px] items-center justify-center rounded-lg border-2 px-1 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.12em] transition-colors disabled:opacity-50",
                mode === m.id
                  ? "border-[color:var(--ink)] bg-[color:var(--arbiter)] text-[color:var(--ink)]"
                  : "border-transparent text-fg-muted",
              )}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="mt-3 space-y-3">
          {mode === "case" ? (
            <div className="space-y-2">
              <span className="block font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Tap a demo case</span>
              {fixtures.length === 0 ? (
                <p className="text-[11px] text-muted">Loading cases…</p>
              ) : (
                fixtures.map((fx) => {
                  const selected = fx.id === fixtureId;
                  return (
                    <button
                      key={fx.id}
                      onClick={() => selectFixture(fx)}
                      disabled={running}
                      className={cn(
                        "btn-tactile w-full rounded-xl border-2 border-[color:var(--ink)] px-3 py-2.5 text-left disabled:opacity-50",
                        selected ? "bg-[color:var(--arbiter)]" : "bg-[color:var(--bg-elevated)]",
                      )}
                    >
                      <span className="block break-words font-mono text-xs font-bold tracking-wider text-[color:var(--ink)]">{fx.title}</span>
                      <span className="mt-0.5 line-clamp-2 block break-words text-[11px] leading-snug text-[color:var(--ink)] opacity-70">
                        {fx.ticket.trim().split("\n")[0]}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          ) : null}

          {mode === "paste" ? (
            <>
              <label className="block">
                <span className="mb-1 block font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Ticket · intent</span>
                <textarea
                  value={ticket}
                  onChange={(e) => {
                    setTicket(e.target.value);
                    clearFixture();
                  }}
                  rows={4}
                  placeholder="What did you ask the AI to build?"
                  className="w-full resize-y rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-3 py-2 font-mono text-xs leading-relaxed"
                />
              </label>
              <label className="block">
                <span className="mb-1 block font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Unified diff</span>
                <textarea
                  value={diff}
                  onChange={(e) => {
                    setDiff(e.target.value);
                    clearFixture();
                  }}
                  rows={8}
                  placeholder="Paste the unified diff the AI produced…"
                  spellCheck={false}
                  className="w-full resize-y rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-3 py-2 font-mono text-[11px] leading-relaxed"
                />
              </label>
              <label className="flex items-center justify-between gap-3 rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-3 py-2.5">
                <span>
                  <span className="block font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg">Quick verdict</span>
                  <span className="block text-[10px] leading-snug text-muted">Skip the live stream — one reliable result (best on mobile data).</span>
                </span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={quickVerdict}
                  aria-label="Quick verdict — skip the live stream"
                  onClick={() => setQuickVerdict(!quickVerdict)}
                  className={cn(
                    "relative h-7 w-12 shrink-0 rounded-full border-2 border-[color:var(--ink)] transition-colors",
                    quickVerdict ? "bg-[color:var(--accent)]" : "bg-[color:var(--bg-elevated)]",
                  )}
                >
                  <span
                    className={cn(
                      "absolute top-0.5 h-5 w-5 rounded-full border-2 border-[color:var(--ink)] bg-white transition-all",
                      quickVerdict ? "left-[22px]" : "left-0.5",
                    )}
                  />
                </button>
              </label>
            </>
          ) : null}

          {mode === "pr" ? (
            <label className="block">
              <span className="mb-1 block font-mono text-[10px] uppercase tracking-[0.18em] text-dim">GitHub PR URL</span>
              <input
                type="url"
                inputMode="url"
                value={prUrl}
                onChange={(e) => setPrUrl(e.target.value)}
                placeholder="https://github.com/owner/repo/pull/123"
                className="w-full rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-3 py-2.5 font-mono text-xs"
              />
              <span className="mt-1 block text-[10px] leading-snug text-muted">Public PRs work without a token. The court fetches the diff + title and returns a one-shot verdict.</span>
            </label>
          ) : null}

          {domains.length > 0 && mode !== "pr" ? (
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-dim">Domains</span>
              {domains.map((d) => (
                <span
                  key={d}
                  className="rounded-full border-2 border-[color:var(--ink)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-[color:var(--ink)]"
                  style={{ background: d === "auth" || d === "security" ? "var(--warden)" : "var(--bg-elevated)" }}
                >
                  {d}
                </span>
              ))}
            </div>
          ) : null}

          <div className="flex gap-2 pt-1">
            <button
              onClick={run}
              disabled={running || !canRun}
              className="btn-tactile flex-1 border-[2.5px] border-[color:var(--ink)] bg-[color:var(--arbiter)] px-3 py-3 font-mono text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--ink)] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {running ? "Deliberating…" : mode === "pr" ? "⚖ Review PR" : "⚖ Convene Tribunal"}
            </button>
            {started ? (
              <button
                onClick={reset}
                disabled={running}
                className="btn-tactile border-[2.5px] border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-4 py-3 font-mono text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--ink)] disabled:opacity-40"
              >
                Reset
              </button>
            ) : null}
          </div>
          {error ? <p className="font-mono text-[11px] text-danger">{error}</p> : null}
        </div>
      </section>

      {/* ── Stage 2 · Deliberation (vertical timeline) ──────────────── */}
      {started ? (
        <section className="glass rounded-2xl p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <SectionTitle icon={<GavelIcon size={16} color="var(--clerk)" />} label="Deliberation" />
            <span
              className="shrink-0 whitespace-nowrap rounded-full border-2 border-[color:var(--ink)] px-2.5 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[color:var(--ink)]"
              style={{ background: bandMode === "live" ? "var(--surveyor)" : "var(--bg-elevated)" }}
            >
              {bandMode === "live" ? "LIVE" : "DEMO"}
            </span>
          </div>

          {/* Roster strip — horizontal scroll on narrow screens so all 7 stay visible */}
          <div className="mb-3 flex gap-3 overflow-x-auto border-b-2 border-[color:var(--ink)] pb-3">
            {roster.map((agent) => {
              const has = spoken.has(agent);
              return (
                <div key={agent} className={cn("flex shrink-0 flex-col items-center gap-0.5 transition-opacity", has ? "opacity-100" : "opacity-40")}>
                  <AgentAvatar agent={agent} size={34} active={current === agent} />
                  <span className="font-mono text-[10px] font-bold tracking-wider text-fg">{agent}</span>
                </div>
              );
            })}
          </div>

          {turns.length === 0 ? (
            <div className="flex items-center gap-2 py-4">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[color:var(--accent)] opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[color:var(--accent)]" />
              </span>
              <p className="text-xs text-muted">{running ? "The chamber is convening…" : "No transcript yet."}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {turns.map((turn) =>
                turn.kind === "recruitment" ? (
                  <div
                    key={turn.id}
                    className="chamber-open rounded-xl border-2 border-[color:var(--ink)] p-3 text-[color:var(--ink)]"
                    style={{ background: "color-mix(in srgb, var(--warden) 30%, #ffffff)", boxShadow: "var(--shadow-ink-sm)" }}
                  >
                    <div className="flex items-start gap-2.5">
                      <span className="shrink-0">
                        <AgentAvatar agent="WARDEN" size={40} active />
                      </span>
                      <div className="min-w-0 flex-1">
                        <span className="inline-block rounded border-2 border-[color:var(--ink)] bg-[color:var(--warden)] px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.14em]">⚖ Witness · WARDEN</span>
                        <p className="mt-1 break-words text-xs font-medium">{turn.text}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <MessageLane key={turn.id} turn={turn} />
                ),
              )}
            </div>
          )}
        </section>
      ) : null}

      {/* ── Stage 3 · Verdict ───────────────────────────────────────── */}
      {verdict ? (
        <section className="glass rounded-2xl p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <SectionTitle icon={<GavelIcon size={16} color="var(--ink)" />} label="Verdict" />
            <button
              onClick={shareVerdict}
              className="btn-tactile rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-[color:var(--ink)]"
            >
              {shareCopied ? "Copied ✓" : "Share verdict"}
            </button>
          </div>
          <div className="flex flex-col gap-4">
            <RulingDetails verdict={verdict} />
          </div>
        </section>
      ) : null}
    </div>
  );
}

function HowItWorks() {
  const steps = [
    { n: 1, icon: <EvidenceTagIcon size={14} color="var(--advocate)" />, title: "Drop the brief", body: "Paste the ticket you gave the AI, plus the diff it produced." },
    { n: 2, icon: <ScalesIcon size={14} color="var(--clerk)" />, title: "The chamber debates", body: "7 specialist agents deliberate live, coordinated over Band — each with one job." },
    { n: 3, icon: <GavelIcon size={14} color="var(--ink)" />, title: "Get the verdict", body: "A trust score, a merge call, and a ledger of what's missing or unauthorized." },
  ];
  return (
    <div className="glass shrink-0 rounded-2xl px-4 py-2">
      <div className="flex items-center gap-2 sm:gap-4">
        {steps.map((s, i) => (
          <div key={s.n} className="flex min-w-0 flex-1 items-center gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-hot font-mono text-[10px] font-bold text-accent">{s.n}</span>
            <div className="flex min-w-0 items-center gap-1.5">
              <span className="shrink-0">{s.icon}</span>
              <span className="truncate font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-fg">{s.title}</span>
              <span className="hidden text-[10px] leading-snug text-muted xl:block">— {s.body}</span>
            </div>
            {i < steps.length - 1 ? <span className="shrink-0 text-dim">→</span> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function InstallPanel() {
  // Git-based install until the PyPI release lands — then the --from arg
  // shortens to "code-tribunal" (keep in sync with install-section.tsx).
  const GIT_FROM = "git+https://github.com/arun3676/code-tribunal.git#subdirectory=apps/api";
  const mcpSnippet = `{
  "mcpServers": {
    "tribunal": {
      "command": "uvx",
      "args": ["--from",
        "${GIT_FROM}",
        "tribunal-mcp"],
      "env": { "GROQ_API_KEY": "<your-key>" }
    }
  }
}`;
  const codexSnippet = `[mcp_servers.tribunal]
command = "uvx"
args = ["--from", "${GIT_FROM}", "tribunal-mcp"]
env = { GROQ_API_KEY = "<your-key>" }`;
  const cliSnippet = `tribunal verify --ticket ticket.md --diff pr.diff`;
  return (
    <div className="border-t-2 border-[color:var(--ink)] pt-3">
      <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-fg-muted">Install · CLI / MCP</p>
      <p className="mb-2 text-[11px] leading-snug text-muted">
        Run the same tribunal from your coding agent or CI — no browser. Bring your own key.
      </p>
      <div className="space-y-2">
        <div>
          <p className="mb-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">Claude Code · Cursor</p>
          <pre className="overflow-x-auto rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-2.5 py-2 font-mono text-[10px] leading-relaxed text-fg">{mcpSnippet}</pre>
        </div>
        <div>
          <p className="mb-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">Codex · ~/.codex/config.toml</p>
          <pre className="overflow-x-auto rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-2.5 py-2 font-mono text-[10px] leading-relaxed text-fg">{codexSnippet}</pre>
        </div>
        <div>
          <p className="mb-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-fg-dim">CLI · gate a PR in CI</p>
          <pre className="overflow-x-auto rounded-lg border-2 border-[color:var(--ink)] bg-[color:var(--bg-overlay)] px-2.5 py-2 font-mono text-[10px] leading-relaxed text-fg">{cliSnippet}</pre>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2">
      {icon}
      <h2 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-fg">{label}</h2>
    </div>
  );
}

function MessageLane({ turn }: { turn: Turn }) {
  const persona = PERSONAS[turn.agent];
  return (
    <div className="lane-in rounded-xl border-2 border-[color:var(--ink)] bg-[color:var(--bg-elevated)] p-4" style={{ borderLeftWidth: "7px", borderLeftColor: persona.color }}>
      <div className="flex items-start gap-3">
        <span className="shrink-0">
          <AgentAvatar agent={turn.agent} size={44} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="font-mono text-sm font-bold tracking-wider text-fg">{turn.agent}</span>
            <span className="text-xs font-semibold italic text-fg-muted">&ldquo;{persona.nickname}&rdquo;</span>
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-fg-dim">· {persona.role}</span>
          </div>
          {turn.text ? <p className="mt-1.5 break-words text-sm font-medium leading-relaxed text-fg">{renderMentions(turn.text)}</p> : null}

          {turn.target && turn.target.length ? (
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-fg-dim">routes to</span>
              {turn.target.map((t) => (
                <span
                  key={t}
                  className="rounded-full border-2 border-[color:var(--ink)] px-2.5 py-0.5 font-mono text-[10px] font-bold tracking-wider text-[color:var(--ink)]"
                  style={{ background: `color-mix(in srgb, ${PERSONAS[t].color} 45%, #ffffff)` }}
                >
                  @{t}
                </span>
              ))}
              <svg width="100%" height="2" className="ml-1 flex-1" aria-hidden>
                <line x1="0" y1="1" x2="100%" y2="1" stroke="var(--ink)" strokeWidth="1.5" className="handoff-line" opacity={0.6} />
              </svg>
            </div>
          ) : null}

          {turn.chips.length ? (
            <div className="mt-2.5 flex flex-col gap-2">
              {turn.chips.map((chip) => (
                <EvidenceChip key={chip.id} chip={chip} />
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function EvidenceChip({ chip }: { chip: Chip }) {
  const color = SEVERITY_COLOR[chip.severity];
  return (
    <div
      className="chip-pop flex items-start gap-2.5 rounded-lg border-2 border-[color:var(--ink)] px-3 py-2"
      style={{ background: `color-mix(in srgb, ${color} 20%, #ffffff)` }}
    >
      <span className="mt-0.5 shrink-0">
        <EvidenceTagIcon size={14} color="var(--ink)" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="rounded-sm border border-[color:var(--ink)] px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-[color:var(--ink)]" style={{ background: color }}>
            {chip.label}
          </span>
          {chip.fileRef ? <span className="break-all font-mono text-[10px] font-semibold text-fg-muted">{chip.fileRef}</span> : null}
        </div>
        <p className="mt-0.5 break-words text-xs font-medium leading-snug text-fg">{chip.detail}</p>
      </div>
    </div>
  );
}

function Findings({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div>
      <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.18em]" style={{ color }}>
        {title}
      </p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-1.5 text-[11px] leading-snug text-fg-muted">
            <span className="shrink-0" style={{ color }}>›</span>
            <span className="min-w-0 break-words">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function LedgerBadge({ decision }: { decision: string }) {
  const map: Record<string, string> = {
    MET: "var(--accent)",
    PARTIAL: "var(--warning)",
    UNMET: "var(--danger)",
    DRIFT: "var(--drift)",
    CONDITION: "var(--warning)",
  };
  const color = map[decision] ?? "var(--fg-muted)";
  return (
    <span className="shrink-0 whitespace-nowrap rounded px-1.5 py-0.5 font-bold tracking-wider" style={{ color, background: `color-mix(in srgb, ${color} 14%, transparent)` }}>
      {decision}
    </span>
  );
}

function renderMentions(text: string) {
  // Highlight @AGENT mentions inline in the agent's persona color.
  const parts = text.split(/(@[A-Z]+)/g);
  return parts.map((part, i) => {
    const name = part.slice(1) as AgentName;
    if (part.startsWith("@") && PERSONAS[name]) {
      return (
        <span
          key={i}
          className="rounded-sm border border-[color:var(--ink)] px-1 font-mono text-[11px] font-bold text-[color:var(--ink)]"
          style={{ background: `color-mix(in srgb, ${PERSONAS[name].color} 50%, #ffffff)` }}
        >
          {part}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}
