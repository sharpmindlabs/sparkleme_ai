import type { BatchSummary, CaseMeta, EngineConfig } from "./types";

// Same-origin "/api" by default (works behind the Vite dev proxy and when the
// engine serves the built UI). Override with VITE_API_BASE for a remote engine.
const API_BASE = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/$/, "");

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`GET ${path} failed: ${res.status} ${detail}`.trim());
  }
  return res.json() as Promise<T>;
}

export function fetchConfig(): Promise<EngineConfig> {
  return getJSON<EngineConfig>("/config");
}

export function fetchCases(): Promise<CaseMeta[]> {
  return getJSON<CaseMeta[]>("/cases");
}

/** Latest batch, or null when the engine has none yet (404). */
export async function fetchResults(): Promise<BatchSummary | null> {
  const res = await fetch(`${API_BASE}/results`);
  if (res.status === 404) return null;
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`GET /results failed: ${res.status} ${detail}`.trim());
  }
  return res.json() as Promise<BatchSummary>;
}

export async function runBatch(
  body: { client_ids?: string[] | null; only_available?: boolean } = {},
): Promise<BatchSummary> {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ only_available: true, ...body }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`POST /run failed: ${res.status} ${detail}`.trim());
  }
  return res.json() as Promise<BatchSummary>;
}

/** URL for the idx-th drape image of a client (0-based). Use as <img src>. */
export function imageUrl(clientId: string, idx: number): string {
  return `${API_BASE}/image/${encodeURIComponent(clientId)}/${idx}`;
}
