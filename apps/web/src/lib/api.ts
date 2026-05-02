export type ModelInfo = {
  id: string;
  provider: string;
  available: boolean;
  display: string;
  color: string;
  vision?: boolean;
};

export type ScanResult = {
  security: {
    vulnerabilities: Array<{
      vulnerability_type: string;
      severity: string;
      description: string;
      line_number: number;
      code_snippet: string;
    }>;
    risk_score: number;
    summary: Record<string, number>;
    recommendations: string[];
  };
  performance: {
    issues: Array<{
      issue_type: string;
      severity: string;
      description: string;
      line_number: number;
      code_snippet: string;
      impact: string;
      suggestion: string;
    }>;
    overall_score: number;
    summary: Record<string, number>;
    recommendations: string[];
    complexity_analysis: Record<string, string | number>;
  };
};

export type StreamEvent = {
  event: string;
  data: any;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

async function* streamSse(path: string, payload: unknown, signal?: AbortSignal): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const parseFrame = (frame: string): StreamEvent | null => {
    const lines = frame.split("\n");
    let event = "message";
    let data = "";
    for (const line of lines) {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      }
      if (line.startsWith("data:")) {
        data += line.slice(5).trim();
      }
    }
    if (!data) {
      return null;
    }
    return { event, data: JSON.parse(data) };
  };
  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const parsed = parseFrame(frame);
      if (parsed) yield parsed;
    }
  }
  buffer += decoder.decode().replace(/\r\n/g, "\n");
  const parsed = parseFrame(buffer);
  if (parsed) yield parsed;
}

export function getHealth() {
  return request<{ status: string; version: string }>("/health", { method: "GET" });
}

export function getModels() {
  return request<ModelInfo[]>("/models", { method: "GET" });
}

export function analyze(payload: { code: string; language?: string; model: string; mode: "quick" | "thorough" }, signal?: AbortSignal) {
  return streamSse("/analyze", payload, signal);
}

export function council(payload: { code: string; language?: string; models: string[]; mode: "quick" | "thorough" }, signal?: AbortSignal) {
  return streamSse("/council", payload, signal);
}

export function scan(payload: { code: string; language?: string }) {
  return request<ScanResult>("/scan", { method: "POST", body: JSON.stringify(payload) });
}

export async function multimodal(payload: { file: File; prompt?: string; model?: string }) {
  const formData = new FormData();
  formData.append("image", payload.file);
  if (payload.prompt) {
    formData.append("prompt", payload.prompt);
  }
  if (payload.model) {
    formData.append("model", payload.model);
  }
  const response = await fetch(`${API_URL}/multimodal`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<{
    analysis: string;
    code_extracted: string;
    suggestions: string[];
    model: string;
  }>;
}
