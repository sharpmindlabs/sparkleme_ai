// Typed REST client for the SparkleMe API (Functional Spec §11). Every call is
// authenticated with the stored JWT. Functions throw ApiError on failure so the
// data layer can fall back to the offline mock backend and surface clear states.

import type {
  Analysis,
  Correction,
  EngineConfig,
  ModelConfig,
  PromptType,
  PromptVersion,
  ReviewBody,
  Session,
  TrainingJob,
  User,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly network = false,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const TOKEN_KEY = "sparkleme.token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: authHeaders(init.headers as Record<string, string> | undefined),
    });
  } catch (e) {
    // Network / CORS / server-down: mark as a network error for graceful fallback.
    throw new ApiError(e instanceof Error ? e.message : "Network error", 0, true);
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new ApiError(`${init.method ?? "GET"} ${path} → ${res.status} ${detail}`.trim(), res.status);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function json(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const api = {
  base: API_BASE,

  // --- Auth ---
  login(email: string, password: string): Promise<Session> {
    return request<Session>("/auth/login", json("POST", { email, password }));
  },

  // --- Analyses ---
  listAnalyses(params: Record<string, string> = {}): Promise<Analysis[]> {
    const qs = new URLSearchParams(params).toString();
    return request<Analysis[]>(`/analyses${qs ? `?${qs}` : ""}`);
  },
  getAnalysis(id: number): Promise<Analysis> {
    return request<Analysis>(`/analyses/${id}`);
  },
  createAnalysis(form: FormData): Promise<Analysis> {
    return request<Analysis>("/analyses", { method: "POST", body: form });
  },
  review(id: number, body: ReviewBody): Promise<Analysis> {
    return request<Analysis>(`/analyses/${id}/review`, json("POST", body));
  },
  rerun(id: number): Promise<Analysis> {
    return request<Analysis>(`/analyses/${id}/rerun`, { method: "POST" });
  },

  // --- Prompts ---
  listPrompts(type: PromptType): Promise<PromptVersion[]> {
    return request<PromptVersion[]>(`/prompts/${type}/versions`);
  },
  createPrompt(type: PromptType, body: { body: string; note: string }): Promise<PromptVersion> {
    return request<PromptVersion>(`/prompts/${type}/versions`, json("POST", body));
  },
  setActivePrompt(type: PromptType, version: string): Promise<void> {
    return request<void>(`/prompts/${type}/active`, json("PUT", { version }));
  },

  // --- Admin: engine / models / users ---
  getEngine(): Promise<EngineConfig> {
    return request<EngineConfig>("/admin/engine");
  },
  setEngine(cfg: EngineConfig): Promise<EngineConfig> {
    return request<EngineConfig>("/admin/engine", json("PUT", cfg));
  },
  listModels(): Promise<ModelConfig[]> {
    return request<ModelConfig[]>("/admin/models");
  },
  patchModel(id: string, patch: Partial<ModelConfig>): Promise<ModelConfig> {
    return request<ModelConfig>(`/admin/models/${id}`, json("PATCH", patch));
  },
  listUsers(): Promise<User[]> {
    return request<User[]>("/admin/users");
  },
  inviteUser(body: { email: string; role: User["role"] }): Promise<User> {
    return request<User>("/admin/users", json("POST", body));
  },
  patchUser(id: string, patch: Partial<User>): Promise<User> {
    return request<User>(`/admin/users/${id}`, json("PATCH", patch));
  },

  // --- Admin: memory / training / metrics ---
  listMemory(): Promise<Correction[]> {
    return request<Correction[]>("/admin/memory");
  },
  expireMemory(id: number): Promise<void> {
    return request<void>(`/admin/memory/${id}`, { method: "DELETE" });
  },
  listJobs(): Promise<TrainingJob[]> {
    return request<TrainingJob[]>("/admin/training/jobs");
  },
  createJob(body: { model: string; method: string }): Promise<TrainingJob> {
    return request<TrainingJob>("/admin/training/jobs", json("POST", body));
  },
  metrics<T>(scope: string): Promise<T> {
    return request<T>(`/metrics/${scope}`);
  },
};
