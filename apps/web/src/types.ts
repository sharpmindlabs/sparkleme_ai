// Domain contracts for the SparkleMe platform app. These mirror the Functional
// Spec output contract (§5.5), data model (§9) and REST sketch (§11).

export type Role = "ADMIN" | "EXPERT" | "ANALYST" | "VIEWER";

export const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Admin",
  EXPERT: "Colour Analysis Expert",
  ANALYST: "Colour Analyst",
  VIEWER: "Viewer",
};

export type UserStatus = "Active" | "Suspended";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  status: UserStatus;
}

export interface Session {
  token: string;
  user: Pick<User, "name" | "email" | "role">;
}

export type Undertone = "Cool" | "Warm";
export type HomeSeason = "Winter" | "Summer" | "Spring" | "Autumn";
export type Confidence = "High" | "Medium" | "Low";

export type AnalysisStatus =
  | "Running"
  | "Pending Review"
  | "Approved"
  | "Corrected"
  | "Needs Human Review"
  | "Conflicting Inputs"
  | "Finalized";

export type ResultStatus =
  | "OK"
  | "INVALID_INPUT"
  | "CONFLICTING_INPUTS"
  | "NEEDS_HUMAN_REVIEW";

export interface DrapeStep {
  step: number;
  winner: string;
  criteria_cited: number[];
  reasoning?: string;
}

export interface Evidence {
  a_eyes: string;
  b_hair: string;
  c_skin: string;
  d_drape_steps: DrapeStep[];
}

export interface ModelVote {
  model: string;
  vote: string;
  raw?: string;
}

export interface EngineSnapshot {
  mode: "single" | "consensus";
  strategy?: string;
  primary?: string;
  models?: string[];
}

/** A single analysis record (list + detail). */
export interface Analysis {
  id: number;
  client: string;
  date: string;
  // Inputs
  hair: string;
  fitzpatrick: string;
  notes?: string;
  tone: string; // demo skin-tone key for the placeholder overlay
  // Result (§5.5)
  result_status: ResultStatus;
  status: AnalysisStatus;
  undertone: Undertone | null;
  home_season: HomeSeason | null;
  ai_result: string | null; // AI consensus flow_result
  expert_result: string | null; // expert-finalised palette (if reviewed)
  confidence: number; // 0..100
  candidate_set: string[];
  evidence: Evidence;
  model_votes: ModelVote[];
  prompt_version: string;
  engine: EngineSnapshot;
  why: string;
  expert_note: string | null;
}

/** Confidence bucket per §5.5 (High / Medium / Low). */
export function confidenceLabel(pct: number): Confidence {
  if (pct >= 88) return "High";
  if (pct >= 70) return "Medium";
  return "Low";
}

export interface PromptVersion {
  version: string;
  date: string;
  author: string;
  note: string;
  accuracy: number | null; // first-pass approval rate while active
  body: string;
  active: boolean;
}

export type PromptType = "analysis" | "audit";

export interface ModelConfig {
  id: string;
  name: string;
  type: "Commercial" | "Open source";
  enabled: boolean;
  weight: number;
  accuracy: number;
  latency: string;
  training: string;
}

export interface EngineConfig {
  mode: "single" | "consensus";
  strategy: string;
  primary: string;
}

export interface Correction {
  id: number;
  palette: string;
  note: string;
  date: string;
  by: string;
}

export interface TrainingJob {
  id: string;
  model: string;
  method: string;
  examples: number;
  status: "Completed" | "Running" | "Live" | "Failed";
  delta: string;
}

export interface ReviewBody {
  verdict: "APPROVE" | "CORRECT";
  palette?: string;
  comments: string;
  influence?: string;
}

export interface RerunLog {
  lines: string[];
  memory: "HIT" | "MISS";
  result: string;
}
