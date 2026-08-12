"""Pydantic v2 request/response contracts for the REST API."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ---- auth ----
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: str


# ---- analyses ----
class AnalysisSummary(BaseModel):
    id: str
    client_label: str
    initiator_id: str
    status: str
    result_status: Optional[str] = None
    undertone: Optional[str] = None
    home_season: Optional[str] = None
    flow_result: Optional[str] = None
    ai_result: Optional[str] = None
    expert_result: Optional[str] = None
    confidence: Optional[str] = None
    memory_hit: bool = False
    prompt_version: Optional[str] = None
    created_at: str


class ModelVoteOut(BaseModel):
    model: str
    vote: str
    raw: Optional[str] = None


class AnalysisDetail(AnalysisSummary):
    candidate_set: list[str] = Field(default_factory=list)
    evidence: dict = Field(default_factory=dict)
    model_votes: list[dict] = Field(default_factory=list)
    engine_config_snapshot: dict = Field(default_factory=dict)
    inputs: dict = Field(default_factory=dict)
    output_contract: dict = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    verdict: str  # APPROVE | CORRECT
    palette: Optional[str] = None
    comments: str = ""
    influence: str = ""


# ---- prompts ----
class PromptVersionOut(BaseModel):
    version: str
    type: str
    author: str
    change_note: str
    active: bool
    created_at: str
    body: Optional[str] = None


class PromptCreate(BaseModel):
    body: str
    change_note: str = ""


class PromptActivate(BaseModel):
    version: str


# ---- admin: engine ----
class EngineConfigOut(BaseModel):
    mode: str
    strategy: str
    primary_model_id: Optional[str] = None


class EngineConfigUpdate(BaseModel):
    mode: Optional[str] = None
    strategy: Optional[str] = None
    primary_model_id: Optional[str] = None


# ---- admin: models ----
class ModelConfigOut(BaseModel):
    model_id: str
    provider: str
    type: str
    enabled: bool
    vote_weight: float
    endpoint: str
    active_version: str
    registry_order: int
    is_primary: bool


class ModelConfigCreate(BaseModel):
    model_id: str
    provider: str
    type: str = "COMMERCIAL"
    enabled: bool = True
    vote_weight: float = 1.0
    endpoint: str = ""
    active_version: str = ""
    registry_order: int = 0
    is_primary: bool = False


class ModelConfigPatch(BaseModel):
    enabled: Optional[bool] = None
    vote_weight: Optional[float] = None
    endpoint: Optional[str] = None
    active_version: Optional[str] = None
    registry_order: Optional[int] = None
    is_primary: Optional[bool] = None


# ---- admin: users ----
class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "ANALYST"


class UserPatch(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None


# ---- admin: training ----
class TrainingJobCreate(BaseModel):
    model_id: str
    method: str = "SFT"


class TrainingJobOut(BaseModel):
    id: str
    model_id: str
    method: str
    example_count: int
    status: str
    golden_set_result: dict
    created_at: str
