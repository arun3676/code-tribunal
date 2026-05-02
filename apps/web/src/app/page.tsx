"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";

import { analyze, council, getModels, multimodal, scan, type ModelInfo, type ScanResult } from "@/lib/api";

const MonacoEditor = dynamic(async () => (await import("@monaco-editor/react")).default, {
  ssr: false,
  loading: () => <div className="panel flex h-[300px] items-center justify-center sm:h-[420px] rounded-2xl text-sm text-fg-dim">Loading editor...</div>,
});

type Mode = "quick" | "thorough";
type View = "solo" | "council";

type VerdictState = {
  raw: string;
  score: number | null;
  bugs: string[];
  suggestions: string[];
  documentation: string;
  fixes: Array<Record<string, any>>;
  done: boolean;
  durationMs: number | null;
  error: string | null;
};

type CouncilEntry = VerdictState & {
  model: string;
  expanded: boolean;
};

type AgreementRow = {
  label: string;
  models: Record<string, boolean | null>;
  agreementCount: number;
};

const EXAMPLES = [
  {
    label: "Python",
    language: "python",
    code: "def divide(a, b):\n    return a / b\n\nprint(divide(10, 0))\n",
  },
  {
    label: "JavaScript",
    language: "javascript",
    code: "export async function handler(req, res) {\n  const user = await db.find(req.query.id);\n  res.json({ user });\n}\n",
  },
  {
    label: "SQL",
    language: "sql",
    code: "SELECT * FROM users WHERE email = 'alice@example.com';\n",
  },
] as const;

const STORAGE_KEY = "code-council-session";

const emptyVerdict = (): VerdictState => ({
  raw: "",
  score: null,
  bugs: [],
  suggestions: [],
  documentation: "",
  fixes: [],
  done: false,
  durationMs: null,
  error: null,
});

function setStatus(value: string) {
  window.dispatchEvent(new CustomEvent("code-council-status", { detail: value }));
}

function normalizeText(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
}

function jaccard(left: string, right: string) {
  const a = new Set(normalizeText(left).split(" ").filter(Boolean));
  const b = new Set(normalizeText(right).split(" ").filter(Boolean));
  if (!a.size && !b.size) return 1;
  if (!a.size || !b.size) return 0;
  const intersection = [...a].filter((item) => b.has(item)).length;
  const union = new Set([...a, ...b]).size;
  return union ? intersection / union : 0;
}

export default function HomePage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const availableModels = useMemo(() => models.filter((model) => model.available), [models]);
  const [view, setView] = useState<View>("solo");
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("auto");
  const [model, setModel] = useState("");
  const [mode, setMode] = useState<Mode>("quick");
  const [soloVerdict, setSoloVerdict] = useState<VerdictState>(emptyVerdict);
  const [isSoloRunning, setIsSoloRunning] = useState(false);
  const [soloLatencyMs, setSoloLatencyMs] = useState(0);
  const [scanEnabled, setScanEnabled] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [councilModels, setCouncilModels] = useState<string[]>([]);
  const [councilVerdicts, setCouncilVerdicts] = useState<Record<string, CouncilEntry>>({});
  const [isCouncilRunning, setIsCouncilRunning] = useState(false);
  const [councilStartedAt, setCouncilStartedAt] = useState(0);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePrompt, setImagePrompt] = useState("Analyze this image and extract code or engineering-relevant details.");
  const [imageModel, setImageModel] = useState("gemini-2.5-flash");
  const [imagePreview, setImagePreview] = useState("");
  const [imageResult, setImageResult] = useState<{ analysis: string; code_extracted: string; suggestions: string[]; model: string } | null>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const soloAbortRef = useRef<AbortController | null>(null);
  const councilAbortRef = useRef<AbortController | null>(null);
  const completedCouncilModelsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    getModels()
      .then((data) => {
        setModels(data);
        const defaults = data.filter((item) => item.available).map((item) => item.id);
        setCouncilModels(defaults.slice(0, 4));
        setModel((current) => current || defaults[0] || "");
      })
      .catch(() => setModels([]));
  }, []);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    try {
      const parsed = JSON.parse(saved) as { code?: string; language?: string; model?: string; mode?: Mode };
      if (parsed.code) setCode(parsed.code);
      if (parsed.language) setLanguage(parsed.language);
      if (parsed.model) setModel(parsed.model);
      if (parsed.mode) setMode(parsed.mode);
    } catch {}
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ code, language, model, mode }));
  }, [code, language, model, mode]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (isSoloRunning) {
        setSoloLatencyMs((value) => value + 100);
      }
    }, 100);
    return () => window.clearInterval(interval);
  }, [isSoloRunning]);

  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      const item = [...(event.clipboardData?.items ?? [])].find((entry) => entry.type.startsWith("image/"));
      if (!item) return;
      const file = item.getAsFile();
      if (!file) return;
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "?" && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        setShowShortcuts((value) => !value);
      }
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        if (view === "solo") {
          void runSolo();
        } else {
          void runCouncil();
        }
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (!availableModels.length) return;
        const ids = availableModels.map((entry) => entry.id);
        const currentIndex = ids.indexOf(model);
        const next = ids[(currentIndex + 1 + ids.length) % ids.length];
        setModel(next);
      }
    };
    window.addEventListener("paste", onPaste);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("paste", onPaste);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [availableModels, model, view, code, councilModels, mode]);

  async function runSolo() {
    if (!code.trim() || !model || isSoloRunning) return;
    const controller = new AbortController();
    soloAbortRef.current = controller;
    setSoloVerdict(emptyVerdict());
    setScanResult(null);
    setIsSoloRunning(true);
    setSoloLatencyMs(0);
    setStatus(`analyzing... ${availableModels.find((item) => item.id === model)?.display ?? model}`);
    if (scanEnabled) {
      scan({ code, language: language === "auto" ? undefined : language })
        .then(setScanResult)
        .catch(() => setScanResult(null));
    }
    try {
      for await (const event of analyze({ code, language: language === "auto" ? undefined : language, model, mode }, controller.signal)) {
        if (event.event === "token") {
          setSoloVerdict((current) => ({ ...current, raw: `${current.raw}${event.data.delta}` }));
        } else if (event.event === "parsed") {
          setSoloVerdict((current) => ({
            ...current,
            score: Number(event.data.quality_score ?? 0),
            bugs: event.data.bugs ?? [],
            suggestions: event.data.suggestions ?? [],
            documentation: event.data.documentation ?? "",
          }));
        } else if (event.event === "fixes") {
          setSoloVerdict((current) => ({ ...current, fixes: event.data ?? [] }));
        } else if (event.event === "done") {
          setSoloVerdict((current) => ({ ...current, done: true, durationMs: Number(event.data.duration_ms ?? 0) }));
        } else if (event.event === "error") {
          setSoloVerdict((current) => ({ ...current, error: String(event.data.message ?? "Analysis failed") }));
        }
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        setSoloVerdict((current) => ({ ...current, error: error instanceof Error ? error.message : "Analysis failed" }));
      }
    } finally {
      setIsSoloRunning(false);
      setStatus(soloVerdict.done ? "ready" : "complete");
    }
  }

  function stopSolo() {
    soloAbortRef.current?.abort();
    setIsSoloRunning(false);
    setStatus("ready");
  }

  async function runCouncil() {
    if (!code.trim() || councilModels.length < 2 || isCouncilRunning) return;
    const controller = new AbortController();
    councilAbortRef.current = controller;
    completedCouncilModelsRef.current = new Set();
    setCouncilStartedAt(Date.now());
    setIsCouncilRunning(true);
    setCouncilVerdicts(
      Object.fromEntries(
        councilModels.map((entry) => [
          entry,
          {
            ...emptyVerdict(),
            model: entry,
            expanded: false,
          },
        ]),
      ),
    );
    setStatus(`council: 0/${councilModels.length} responding`);
    try {
      for await (const event of council({ code, language: language === "auto" ? undefined : language, models: councilModels, mode }, controller.signal)) {
        if (event.event === "token") {
          setCouncilVerdicts((current) => ({
            ...current,
            [event.data.model]: {
              ...current[event.data.model],
              raw: `${current[event.data.model]?.raw ?? ""}${event.data.delta}`,
            },
          }));
        } else if (event.event === "parsed") {
          setCouncilVerdicts((current) => ({
            ...current,
            [event.data.model]: {
              ...current[event.data.model],
              score: Number(event.data.quality_score ?? 0),
              bugs: event.data.bugs ?? [],
              suggestions: event.data.suggestions ?? [],
              documentation: event.data.documentation ?? "",
            },
          }));
        } else if (event.event === "fixes") {
          setCouncilVerdicts((current) => ({
            ...current,
            [event.data.model]: {
              ...current[event.data.model],
              fixes: event.data.items ?? [],
            },
          }));
        } else if (event.event === "done") {
          completedCouncilModelsRef.current.add(event.data.model);
          setCouncilVerdicts((current) => {
            const updated: Record<string, CouncilEntry> = {
              ...current,
              [event.data.model]: {
                ...current[event.data.model],
                done: true,
                durationMs: Number(event.data.duration_ms ?? 0),
              },
            };
            return updated;
          });
          setStatus(`council: ${completedCouncilModelsRef.current.size}/${councilModels.length} responding`);
        } else if (event.event === "error") {
          completedCouncilModelsRef.current.add(event.data.model);
          setCouncilVerdicts((current) => ({
            ...current,
            [event.data.model]: {
              ...current[event.data.model],
              error: String(event.data.message ?? "Model unresponsive"),
              done: true,
            },
          }));
          setStatus(`council: ${completedCouncilModelsRef.current.size}/${councilModels.length} responding`);
        } else if (event.event === "all_done") {
          setStatus(`complete in ${(Number(event.data.total_duration_ms ?? 0) / 1000).toFixed(1)}s`);
        }
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        setStatus(error instanceof Error ? error.message : "Council failed");
      }
    } finally {
      setIsCouncilRunning(false);
    }
  }

  function stopCouncil() {
    councilAbortRef.current?.abort();
    setIsCouncilRunning(false);
    setStatus("ready");
  }

  async function handleImageAnalyze() {
    if (!imageFile || imageLoading) return;
    setImageLoading(true);
    try {
      const result = await multimodal({ file: imageFile, prompt: imagePrompt, model: imageModel });
      setImageResult(result);
    } catch {
      setImageResult(null);
    } finally {
      setImageLoading(false);
    }
  }

  const consensus = useMemo(() => {
    const scores = Object.values(councilVerdicts)
      .map((entry) => entry.score)
      .filter((entry): entry is number => typeof entry === "number");
    if (!scores.length) return null;
    const spread = Math.max(...scores) - Math.min(...scores);
    if (spread <= 5) return { label: "CONSENSUS", color: "var(--accent)", spread };
    if (spread <= 20) return { label: "MIXED", color: "var(--warning)", spread };
    return { label: "DIVIDED", color: "var(--danger)", spread };
  }, [councilVerdicts]);

  const agreementRows = useMemo(() => {
    const buckets: Array<{ label: string; models: Record<string, boolean | null> }> = [];
    const modelIds = councilModels;
    for (const modelId of modelIds) {
      const verdict = councilVerdicts[modelId];
      const issues = [...(verdict?.bugs ?? []), ...(verdict?.suggestions ?? [])];
      if (verdict?.error) {
        continue;
      }
      for (const issue of issues) {
        const existing = buckets.find((bucket) => jaccard(bucket.label, issue) >= 0.55);
        if (existing) {
          if (issue.length > existing.label.length) existing.label = issue;
          existing.models[modelId] = true;
        } else {
          buckets.push({
            label: issue,
            models: Object.fromEntries(modelIds.map((entry) => [entry, false])),
          });
          buckets[buckets.length - 1].models[modelId] = true;
        }
      }
    }
    const rows: AgreementRow[] = buckets.map((bucket) => ({
      ...bucket,
      agreementCount: Object.values(bucket.models).filter(Boolean).length,
    }));
    return rows.sort((left, right) => right.agreementCount - left.agreementCount);
  }, [councilVerdicts, councilModels]);

  const councilCompleted = (Object.values(councilVerdicts) as CouncilEntry[]).filter((entry) => entry.done).length;
  const councilProgress = councilModels.length ? (councilCompleted / councilModels.length) * 100 : 0;

  return (
    <div className="space-y-5 pb-16">
      <section className="panel rounded-2xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-fg-muted">Code Council</div>
            <h1 className="mt-2 text-3xl font-semibold">See how the models think.</h1>
            <p className="mt-2 max-w-3xl text-sm text-fg-muted">
              Paste code, stream one model or a council of models, and compare where they agree or diverge.
            </p>
          </div>
          <div className="flex gap-2 rounded-xl border border-[color:var(--border)] bg-[rgba(10,15,10,0.95)] p-1">
            {(["solo", "council"] as const).map((entry) => (
              <button
                key={entry}
                onClick={() => setView(entry)}
                className={`rounded-lg px-4 py-2 font-mono text-xs uppercase tracking-[0.18em] ${view === entry ? "bg-[color:var(--accent-soft)] text-accent" : "text-fg-muted"}`}
              >
                {entry}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="panel rounded-2xl p-4">
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Drop Image</div>
          <div className="mt-3 flex flex-col gap-3 md:flex-row">
            <div className="flex-1 rounded-xl border border-dashed border-[color:var(--border-hot)] p-4">
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (!file) return;
                  setImageFile(file);
                  setImagePreview(URL.createObjectURL(file));
                }}
              />
              <p className="mt-2 text-sm text-fg-muted">Paste an image anywhere on the page or choose a file.</p>
              {imagePreview ? <img src={imagePreview} alt="Upload preview" className="mt-4 max-h-48 rounded-lg border border-[color:var(--border)] object-contain" /> : null}
            </div>
            <div className="flex-1 space-y-3">
              <select value={imageModel} onChange={(event) => setImageModel(event.target.value)} className="w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--bg-overlay)] px-3 py-2 text-sm">
                {availableModels.filter((entry) => entry.vision).map((entry) => (
                  <option key={entry.id} value={entry.id}>{entry.display}</option>
                ))}
              </select>
              <textarea value={imagePrompt} onChange={(event) => setImagePrompt(event.target.value)} className="h-28 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--bg-overlay)] px-3 py-2 text-sm" />
              <button onClick={() => void handleImageAnalyze()} disabled={!imageFile || imageLoading} className="rounded-lg border border-[color:var(--border-hot)] bg-[color:var(--accent-soft)] px-4 py-2 text-sm text-fg disabled:opacity-40">
                {imageLoading ? "Analyzing..." : "Analyze Image"}
              </button>
            </div>
          </div>
          {imageResult ? (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-overlay)] p-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Extracted Code</div>
                <pre className="mt-3 overflow-auto whitespace-pre-wrap font-mono text-xs text-fg">{imageResult.code_extracted || "No code extracted."}</pre>
                {imageResult.code_extracted ? (
                  <button
                    onClick={() => {
                      setCode(imageResult.code_extracted);
                      setView("solo");
                    }}
                    className="mt-3 rounded-lg border border-[color:var(--border-hot)] px-3 py-2 text-xs font-mono uppercase tracking-[0.16em] text-accent"
                  >
                    Analyze This
                  </button>
                ) : null}
              </div>
              <div className="rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-overlay)] p-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Suggestions</div>
                <div className="mt-3 space-y-2 text-sm text-fg-muted">
                  {imageResult.suggestions.length ? imageResult.suggestions.map((item) => <div key={item}>- {item}</div>) : <div>No suggestions extracted.</div>}
                </div>
              </div>
            </div>
          ) : null}
        </div>

        <div className="panel rounded-2xl p-4">
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-muted">Shortcuts</div>
          <div className="mt-4 grid gap-3 text-sm text-fg-muted">
            <div><span className="kbd">Ctrl/Cmd + Enter</span> run current view</div>
            <div><span className="kbd">Ctrl/Cmd + K</span> cycle to the next model</div>
            <div><span className="kbd">?</span> toggle shortcut overlay</div>
          </div>
          <div className="mt-6 rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-overlay)] p-4 text-sm text-fg-muted">
            Static scan runs regex + AST rules in parallel with solo analysis and renders security/performance findings above the verdict.
          </div>
        </div>
      </section>

      <section className={`grid grid-cols-1 gap-4 ${view === "solo" ? "lg:grid-cols-[1.6fr_1fr]" : "lg:grid-cols-2"}`}>
        <div className="space-y-4">
          <div className="panel rounded-2xl p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                <select value={language} onChange={(event) => setLanguage(event.target.value)} className="rounded-lg border border-[color:var(--border)] bg-[color:var(--bg-overlay)] px-3 py-2 text-sm">
                  <option value="auto">Auto</option>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="typescript">TypeScript</option>
                  <option value="sql">SQL</option>
                  <option value="go">Go</option>
                  <option value="rust">Rust</option>
                </select>
                <div className="flex rounded-lg border border-[color:var(--border)] bg-[color:var(--bg-overlay)] p-1 text-xs font-mono uppercase tracking-[0.16em]">
                  <button onClick={() => setMode("quick")} className={`rounded-md px-3 py-1 ${mode === "quick" ? "bg-[color:var(--accent-soft)] text-accent" : "text-fg-muted"}`}>Quick</button>
                  <button onClick={() => setMode("thorough")} className={`rounded-md px-3 py-1 ${mode === "thorough" ? "bg-[color:var(--accent-soft)] text-accent" : "text-fg-muted"}`}>Thorough</button>
                </div>
                {view === "solo" ? (
                  <label className="flex items-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--bg-overlay)] px-3 py-2 text-sm text-fg-muted">
                    <input type="checkbox" checked={scanEnabled} onChange={(event) => setScanEnabled(event.target.checked)} />
                    Static Scan
                  </label>
                ) : null}
              </div>
              <div className="font-mono text-xs uppercase tracking-[0.16em] text-fg-muted">{code.length} chars</div>
            </div>
            <MonacoEditor
              height="clamp(280px, 50vh, 480px)"
              theme="vs-dark"
              language={language === "auto" ? "python" : language}
              value={code}
              onChange={(value: string | undefined) => setCode(value ?? "")}
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                fontLigatures: true,
                wordWrap: "on",
                bracketPairColorization: { enabled: true },
              }}
            />
            {!code.trim() ? (
              <div className="mt-4 rounded-xl border border-dashed border-[color:var(--border)] p-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-dim">Awaiting Input</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {EXAMPLES.map((entry) => (
                    <button
                      key={entry.label}
                      onClick={() => {
                        setCode(entry.code);
                        setLanguage(entry.language);
                      }}
                      className="rounded-lg border border-[color:var(--border-hot)] px-3 py-2 text-xs font-mono uppercase tracking-[0.16em] text-accent"
                    >
                      Load {entry.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          {view === "solo" ? (
            <div className="panel flex flex-wrap items-center gap-3 rounded-2xl p-4">
              <select value={model} onChange={(event) => setModel(event.target.value)} className="w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--bg-overlay)] px-3 py-2 text-sm sm:w-auto sm:min-w-56">
                {availableModels.map((entry) => (
                  <option key={entry.id} value={entry.id}>{entry.display}</option>
                ))}
              </select>
              <button onClick={() => void runSolo()} disabled={!code.trim() || !model || isSoloRunning} className="rounded-lg border border-[color:var(--border-hot)] bg-[color:var(--accent-soft)] px-5 py-2 text-sm text-fg disabled:opacity-40">
                {isSoloRunning ? "ANALYZING" : "ANALYZE"}
              </button>
              {isSoloRunning ? (
                <button onClick={stopSolo} className="rounded-lg border border-[color:var(--danger)] px-4 py-2 text-sm text-danger">STOP</button>
              ) : null}
            </div>
          ) : (
            <div className="panel rounded-2xl p-4">
              <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Models in Council</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {availableModels.map((entry) => {
                  const active = councilModels.includes(entry.id);
                  return (
                    <button
                      key={entry.id}
                      onClick={() => {
                        setCouncilModels((current) => {
                          if (active) return current.filter((item) => item !== entry.id);
                          if (current.length >= 4) return current;
                          return [...current, entry.id];
                        });
                      }}
                      className={`rounded-full border px-3 py-2 text-xs font-mono uppercase tracking-[0.14em] ${active ? "border-[color:var(--border-hot)] bg-[color:var(--accent-soft)] text-accent" : "border-[color:var(--border)] text-fg-muted"}`}
                    >
                      {entry.display}
                    </button>
                  );
                })}
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-[color:var(--bg-overlay)]">
                <div className="h-full bg-[color:var(--accent)] transition-all" style={{ width: `${councilProgress}%` }} />
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <button onClick={() => void runCouncil()} disabled={!code.trim() || councilModels.length < 2 || isCouncilRunning} className="rounded-lg border border-[color:var(--border-hot)] bg-[color:var(--accent-soft)] px-5 py-2 text-sm text-fg disabled:opacity-40">
                  {isCouncilRunning ? `RUNNING — ${councilCompleted}/${councilModels.length} complete` : "ANALYZE COUNCIL"}
                </button>
                {isCouncilRunning ? <button onClick={stopCouncil} className="rounded-lg border border-[color:var(--danger)] px-4 py-2 text-sm text-danger">STOP</button> : null}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          {view === "solo" ? (
            <div className="panel rounded-2xl p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Verdict</div>
                  <div className="mt-2 text-lg font-semibold">{availableModels.find((entry) => entry.id === model)?.display ?? "Select a model"}</div>
                </div>
                <div className="font-mono text-sm text-fg-muted">{isSoloRunning ? `${(soloLatencyMs / 1000).toFixed(1)}s` : soloVerdict.durationMs ? `${(soloVerdict.durationMs / 1000).toFixed(1)}s` : "idle"}</div>
              </div>
              {scanEnabled && scanResult ? (
                <div className="mt-4 rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-overlay)] p-4">
                  <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Static Scan</div>
                  <div className="mt-3 space-y-3 text-sm">
                    <div>
                      <div className="text-danger">Security · risk {scanResult.security.risk_score}</div>
                      <div className="mt-1 space-y-1 text-fg-muted">
                        {scanResult.security.vulnerabilities.length ? scanResult.security.vulnerabilities.map((item) => <div key={`${item.vulnerability_type}-${item.line_number}`}>- {item.description}</div>) : <div>No security findings.</div>}
                      </div>
                    </div>
                    <div>
                      <div className="text-warning">Performance · score {scanResult.performance.overall_score}</div>
                      <div className="mt-1 space-y-1 text-fg-muted">
                        {scanResult.performance.issues.length ? scanResult.performance.issues.map((item) => <div key={`${item.issue_type}-${item.line_number}`}>- {item.description}</div>) : <div>No performance findings.</div>}
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}
              {soloVerdict.raw || soloVerdict.score !== null || soloVerdict.error ? (
                <div className="mt-4 space-y-4">
                  <section>
                    <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Score</div>
                    <div className="mt-2 h-6 overflow-hidden rounded-full bg-[color:var(--bg-overlay)]">
                      <div className="h-full bg-[color:var(--accent)] transition-all duration-700" style={{ width: `${soloVerdict.score ?? 0}%` }} />
                    </div>
                    <div className="mt-2 font-mono text-3xl text-fg">{soloVerdict.score ?? "--"}</div>
                  </section>
                  <section>
                    <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Bugs</div>
                    <div className="mt-2 space-y-2 text-sm text-fg-muted">
                      {soloVerdict.bugs.length ? soloVerdict.bugs.map((item) => <div key={item} className="text-danger">- {item}</div>) : <div className="text-fg-dim">no bugs detected</div>}
                    </div>
                  </section>
                  <section>
                    <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Suggestions</div>
                    <div className="mt-2 space-y-2 text-sm text-fg-muted">
                      {soloVerdict.suggestions.length ? soloVerdict.suggestions.map((item) => <div key={item} className="text-fg">- {item}</div>) : <div className="text-fg-dim">no suggestions detected</div>}
                    </div>
                  </section>
                  {mode === "thorough" ? (
                    <section>
                      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Fixes</div>
                      <div className="mt-2 space-y-3">
                        {soloVerdict.fixes.length ? soloVerdict.fixes.map((item) => (
                          <div key={item.issue_id} className="rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-overlay)] p-3">
                            <div className="font-mono text-xs uppercase tracking-[0.14em] text-accent">{item.title}</div>
                            <div className="mt-2 text-sm text-fg-muted">{item.explanation}</div>
                            <pre className="mt-3 overflow-auto whitespace-pre-wrap rounded-lg bg-black/30 p-3 font-mono text-xs text-fg">{item.diff}</pre>
                          </div>
                        )) : <div className="text-sm text-fg-dim">No fixes generated.</div>}
                      </div>
                    </section>
                  ) : null}
                  <details className="rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-overlay)] p-4">
                    <summary className="cursor-pointer font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Raw Stream</summary>
                    <pre className="mt-3 overflow-auto whitespace-pre-wrap font-mono text-xs text-fg">{soloVerdict.raw || "No raw stream yet."}</pre>
                  </details>
                  {soloVerdict.error ? <div className="rounded-xl border border-[color:var(--danger)] px-4 py-3 text-sm text-danger">{soloVerdict.error}</div> : null}
                </div>
              ) : (
                <div className="mt-8 rounded-xl border border-dashed border-[color:var(--border)] p-8 text-center font-mono text-sm uppercase tracking-[0.22em] text-fg-dim">Awaiting Input</div>
              )}
            </div>
          ) : councilModels.length < 2 ? (
            <div className="panel rounded-2xl p-8 text-center font-mono text-sm uppercase tracking-[0.2em] text-fg-dim">Council requires two or more participants</div>
          ) : (
            <div className="space-y-4">
              <div className="panel rounded-2xl p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Consensus Ribbon</div>
                  <div className="font-mono text-xs text-fg-muted">{isCouncilRunning ? `${((Date.now() - councilStartedAt) / 1000).toFixed(1)}s` : "idle"}</div>
                </div>
                <div className="mt-3 rounded-full px-4 py-3 font-mono text-sm uppercase tracking-[0.2em] text-black" style={{ background: consensus?.color ?? "var(--bg-overlay)", color: consensus ? "#041108" : "var(--fg-muted)" }}>
                  {consensus ? `${consensus.label} · spread ${consensus.spread.toFixed(1)}` : "Waiting for model scores"}
                </div>
              </div>
              <div className={`grid grid-cols-1 gap-3 sm:grid-cols-2 ${councilModels.length >= 4 ? "xl:grid-cols-4" : councilModels.length === 3 ? "xl:grid-cols-3" : ""}`}>
                {councilModels.map((entry) => {
                  const verdict = councilVerdicts[entry] ?? { ...emptyVerdict(), model: entry, expanded: false };
                  const modelInfo = models.find((item) => item.id === entry);
                  return (
                    <div key={entry} className="panel rounded-2xl p-4" style={{ borderLeft: `2px solid ${modelInfo?.color ?? "var(--border-hot)"}` }}>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">{modelInfo?.display ?? entry}</div>
                          <div className="mt-1 font-mono text-xs text-fg-muted">{verdict.durationMs ? `${(verdict.durationMs / 1000).toFixed(1)}s` : verdict.done ? "done" : "streaming"}</div>
                        </div>
                        <button onClick={() => setCouncilVerdicts((current) => ({ ...current, [entry]: { ...current[entry], expanded: !current[entry]?.expanded } }))} className="rounded-md border border-[color:var(--border)] px-3 py-2 font-mono text-xs text-fg-muted">v</button>
                      </div>
                      <div className="mt-3 h-4 overflow-hidden rounded-full bg-[color:var(--bg-overlay)]">
                        <div className="h-full bg-[color:var(--accent)] transition-all duration-700" style={{ width: `${verdict.score ?? 0}%` }} />
                      </div>
                      <div className="mt-2 font-mono text-2xl">{verdict.score ?? "--"}</div>
                      <div className="mt-3 flex gap-2 text-[11px] uppercase tracking-[0.16em]">
                        <span className="rounded-full border border-[color:var(--border)] px-2 py-1 text-danger">bugs {verdict.bugs.length}</span>
                        <span className="rounded-full border border-[color:var(--border)] px-2 py-1 text-accent">tips {verdict.suggestions.length}</span>
                      </div>
                      {verdict.expanded ? (
                        <div className="mt-4 space-y-3 text-sm text-fg-muted">
                          <div>{verdict.bugs.length ? verdict.bugs.map((item) => <div key={item} className="text-danger">- {item}</div>) : <div>No bugs detected.</div>}</div>
                          <div>{verdict.suggestions.length ? verdict.suggestions.map((item) => <div key={item}>- {item}</div>) : <div>No suggestions.</div>}</div>
                        </div>
                      ) : null}
                      {verdict.error ? <div className="mt-3 rounded-xl border border-[color:var(--danger)] px-3 py-2 text-sm text-danger">MODEL UNRESPONSIVE</div> : null}
                    </div>
                  );
                })}
              </div>
              {agreementRows.length ? (
                <div className="panel rounded-2xl p-4">
                  <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Agreement Matrix</div>
                  <div className="mt-3 overflow-auto">
                    <table className="min-w-full border-separate border-spacing-y-2 text-sm">
                      <thead>
                        <tr className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">
                          <th className="px-3 py-2 text-left">Issue</th>
                          {councilModels.map((entry) => <th key={entry} className="px-3 py-2 text-left">{models.find((item) => item.id === entry)?.provider ?? entry}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {agreementRows.map((row) => (
                          <tr key={row.label} className="bg-[color:var(--bg-elevated)]">
                            <td className="rounded-l-xl px-3 py-3 text-fg">{row.label}</td>
                            {councilModels.map((entry, index) => (
                              <td key={`${row.label}-${entry}`} className={`px-3 py-3 font-mono ${index === councilModels.length - 1 ? "rounded-r-xl" : ""}`}>
                                {councilVerdicts[entry]?.error ? <span className="text-fg-dim">—</span> : row.models[entry] ? <span className="text-accent">✓</span> : <span className="text-fg-dim">✗</span>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-3 text-xs text-fg-dim">Issues clustered by lexical similarity — interpretation may vary.</div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </section>

      {showShortcuts ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/65 px-4" onClick={() => setShowShortcuts(false)}>
          <div className="panel w-full max-w-xl rounded-2xl p-5" onClick={(event) => event.stopPropagation()}>
            <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-fg-muted">man shortcuts</div>
            <div className="mt-4 space-y-3 font-mono text-sm text-fg">
              <div>Ctrl/Cmd + Enter ...... Run current view</div>
              <div>Ctrl/Cmd + K .......... Switch to next available model</div>
              <div>? ..................... Toggle this overlay</div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
