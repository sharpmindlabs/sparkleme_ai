"""SQLAlchemy ORM models — Data Model §9 (SQLite/JSON substitution).

Vectors are stored as JSON arrays (pgvector substitution). Enums are stored as
strings via SQLAlchemy ``Enum``.
"""
from __future__ import annotations
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, ForeignKey, DateTime, Enum as SAEnum, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .domain.state_machine import AnalysisStatus


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- enums
class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    EXPERT = "EXPERT"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Verdict(str, enum.Enum):
    APPROVE = "APPROVE"
    CORRECT = "CORRECT"


class AuditVerdict(str, enum.Enum):
    APPROVE = "APPROVE"
    REVISE = "REVISE"
    REJECT = "REJECT"


class EngineMode(str, enum.Enum):
    SINGLE = "single"
    CONSENSUS = "consensus"


class ConsensusStrategy(str, enum.Enum):
    WEIGHTED_MAJORITY = "weighted_majority"
    AUDITOR_SCORED = "auditor_scored"
    UNANIMITY = "unanimity"


class ModelType(str, enum.Enum):
    COMMERCIAL = "COMMERCIAL"
    OPEN_SOURCE = "OPEN_SOURCE"


class PromptType(str, enum.Enum):
    ANALYSIS = "ANALYSIS"
    AUDIT = "AUDIT"


class TrainingMethod(str, enum.Enum):
    SFT = "SFT"
    DPO = "DPO"
    PROVIDER_FT = "PROVIDER_FT"
    DISTILL = "DISTILL"


class TrainingStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"


# --------------------------------------------------------------------------- tables
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[Role] = mapped_column(SAEnum(Role))
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="initiator")


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    initiator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    client_label: Mapped[str] = mapped_column(String, default="")
    status: Mapped[AnalysisStatus] = mapped_column(SAEnum(AnalysisStatus), default=AnalysisStatus.DRAFT)
    result_status: Mapped[str | None] = mapped_column(String, nullable=True)  # OK/INVALID_INPUT/...
    undertone: Mapped[str | None] = mapped_column(String, nullable=True)
    home_season: Mapped[str | None] = mapped_column(String, nullable=True)
    flow_result: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)  # High/Medium/Low
    candidate_set: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    model_votes: Mapped[list] = mapped_column(JSON, default=list)
    prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    engine_config_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_result: Mapped[str | None] = mapped_column(String, nullable=True)  # original AI palette (pre-correction)
    expert_result: Mapped[str | None] = mapped_column(String, nullable=True)
    memory_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    initiator: Mapped["User"] = relationship(back_populates="analyses")
    input: Mapped["AnalysisInput"] = relationship(back_populates="analysis", uselist=False,
                                                  cascade="all, delete-orphan")
    model_runs: Mapped[list["ModelRun"]] = relationship(back_populates="analysis",
                                                        cascade="all, delete-orphan")
    consensus: Mapped["ConsensusResult"] = relationship(back_populates="analysis", uselist=False,
                                                        cascade="all, delete-orphan")
    reviews: Mapped[list["ExpertReview"]] = relationship(back_populates="analysis",
                                                        cascade="all, delete-orphan")
    audits: Mapped[list["AuditRecord"]] = relationship(back_populates="analysis",
                                                       cascade="all, delete-orphan")


class AnalysisInput(Base):
    __tablename__ = "analysis_inputs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    image_uri: Mapped[str] = mapped_column(String, default="")  # "encrypted at rest" (stubbed)
    image_embedding: Mapped[list] = mapped_column(JSON, default=list)  # vector -> JSON
    image_sha256: Mapped[str] = mapped_column(String, default="")
    hair_colour: Mapped[str] = mapped_column(String)
    fitzpatrick: Mapped[str] = mapped_column(String)  # I..VI
    freeform_notes: Mapped[str] = mapped_column(Text, default="")  # weak signal only
    crop_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    analysis: Mapped["Analysis"] = relationship(back_populates="input")


class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    model_id: Mapped[str] = mapped_column(String)
    vote: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_response: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    seed: Mapped[int] = mapped_column(Integer, default=0)
    accepted: Mapped[bool] = mapped_column(Boolean, default=True)  # within candidate set?

    analysis: Mapped["Analysis"] = relationship(back_populates="model_runs")


class ConsensusResult(Base):
    __tablename__ = "consensus_results"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    strategy: Mapped[str] = mapped_column(String)
    vote_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    final_palette: Mapped[str | None] = mapped_column(String, nullable=True)

    analysis: Mapped["Analysis"] = relationship(back_populates="consensus")


class ExpertReview(Base):
    __tablename__ = "expert_reviews"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    expert_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    verdict: Mapped[Verdict] = mapped_column(SAEnum(Verdict))
    comments: Mapped[str] = mapped_column(Text, default="")
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    analysis: Mapped["Analysis"] = relationship(back_populates="reviews")
    correction: Mapped["Correction"] = relationship(back_populates="review", uselist=False,
                                                    cascade="all, delete-orphan")


class Correction(Base):
    __tablename__ = "corrections"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    review_id: Mapped[str] = mapped_column(ForeignKey("expert_reviews.id"))
    corrected_palette: Mapped[str] = mapped_column(String)
    prompt_influence: Mapped[str] = mapped_column(Text, default="")
    reasoning: Mapped[str] = mapped_column(Text, default="")

    review: Mapped["ExpertReview"] = relationship(back_populates="correction")


class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    embedding_key: Mapped[list] = mapped_column(JSON, default=list)  # vector -> JSON
    input_key: Mapped[dict] = mapped_column(JSON, default=dict)      # {hair_colour, fitzpatrick}
    verified_palette: Mapped[str] = mapped_column(String)
    home_season: Mapped[str | None] = mapped_column(String, nullable=True)
    undertone: Mapped[str | None] = mapped_column(String, nullable=True)
    expert_note: Mapped[str] = mapped_column(Text, default="")
    match_threshold: Mapped[float] = mapped_column(Float, default=0.92)
    source_analysis_id: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=_now)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    version: Mapped[str] = mapped_column(String, index=True)  # e.g. "v1"
    type: Mapped[PromptType] = mapped_column(SAEnum(PromptType))
    body: Mapped[str] = mapped_column(Text)  # immutable
    author: Mapped[str] = mapped_column(String, default="")
    change_note: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ModelConfig(Base):
    __tablename__ = "model_configs"
    model_id: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String)
    type: Mapped[ModelType] = mapped_column(SAEnum(ModelType))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    vote_weight: Mapped[float] = mapped_column(Float, default=1.0)
    endpoint: Mapped[str] = mapped_column(String, default="")
    active_version: Mapped[str] = mapped_column(String, default="")
    registry_order: Mapped[int] = mapped_column(Integer, default=0)  # deterministic tie-break
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)  # single-mode primary


class EngineConfig(Base):
    """Platform-wide execution mode (§FR-7.1). Singleton row id='default'."""
    __tablename__ = "engine_config"
    id: Mapped[str] = mapped_column(String, primary_key=True, default="default")
    mode: Mapped[EngineMode] = mapped_column(SAEnum(EngineMode), default=EngineMode.CONSENSUS)
    strategy: Mapped[ConsensusStrategy] = mapped_column(SAEnum(ConsensusStrategy),
                                                        default=ConsensusStrategy.WEIGHTED_MAJORITY)
    primary_model_id: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class AuditRecord(Base):
    __tablename__ = "audit_records"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    verdict: Mapped[AuditVerdict] = mapped_column(SAEnum(AuditVerdict))
    failed_checks: Mapped[list] = mapped_column(JSON, default=list)
    audit_prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    analysis: Mapped["Analysis"] = relationship(back_populates="audits")


class TrainingJob(Base):
    __tablename__ = "training_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    model_id: Mapped[str] = mapped_column(String)
    method: Mapped[TrainingMethod] = mapped_column(SAEnum(TrainingMethod))
    example_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[TrainingStatus] = mapped_column(SAEnum(TrainingStatus), default=TrainingStatus.QUEUED)
    golden_set_result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AuditLog(Base):
    """Generic admin/expert action audit trail (NFR-Auditability)."""
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String, default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class IdempotencyRecord(Base):
    """Stores the outcome of a mutating request keyed by Idempotency-Key."""
    __tablename__ = "idempotency_records"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    endpoint: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str | None] = mapped_column(String, nullable=True)
    response_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
