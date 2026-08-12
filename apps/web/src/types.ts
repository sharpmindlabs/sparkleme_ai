// Contracts mirrored from the FastAPI engine (services/inference_engine/app/schema.py).

export type MatchKind =
  | "exact"
  | "boundary"
  | "miss"
  | "error"
  | "no_ground_truth";

export interface DrapeStep {
  step: string;
  winner: string;
  criteria_cited: number[];
  reasoning: string;
}

export interface InferenceResult {
  home_season: string | null;
  flow_result: string | null;
  leaning: string | null;
  confidence: string | null;
  steps: DrapeStep[];
  final_reasoning: string;
  valid: boolean;
  validation_error: string | null;
}

export interface CaseResult {
  client_id: string;
  test_id: number | null;
  model: string;
  carol_result: string | null;
  carol_primary: string | null;
  carol_accepted: string[];
  predicted: string | null;
  match: boolean;
  match_kind: MatchKind;
  confidence: string | null;
  latency_ms: number | null;
  error: string | null;
  result: InferenceResult | null;
}

export interface BatchSummary {
  model: string;
  provider: string;
  total: number;
  scored: number;
  exact: number;
  boundary: number;
  misses: number;
  errors: number;
  accuracy: number; // 0..1  (exact + boundary) / scored
  exact_accuracy: number; // 0..1
  confusion: Record<string, Record<string, number>>;
  cases: CaseResult[];
}

export interface EngineConfig {
  provider: string;
  model: string;
  images_root: string;
  available_clients: string[];
  available_count: number;
  palettes: string[];
  flows_by_season: Record<string, string[]>;
}

export interface CaseMeta {
  test_id: number | null;
  client_id: string;
  carol_result: string | null;
  ai_first_pass: string | null;
  correct_first_time: string | null;
  has_images: boolean;
}
