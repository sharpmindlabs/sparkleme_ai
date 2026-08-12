"""Pydantic contracts for the inference engine's structured output and eval records."""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

from .palettes import PALETTES, HOME_SEASONS

Confidence = Literal["High", "Medium", "Low"]


class DrapeStep(BaseModel):
    step: str
    winner: str
    criteria_cited: list[int] = Field(default_factory=list)  # subset of 1..7
    reasoning: str = ""


class InferenceResult(BaseModel):
    """The model's structured verdict for one client."""
    home_season: Optional[str] = None
    flow_result: Optional[str] = None          # one of the 10 palettes
    leaning: Optional[str] = None              # neighbouring palette or None
    confidence: Confidence = "Low"
    steps: list[DrapeStep] = Field(default_factory=list)
    final_reasoning: str = ""

    # provenance (filled by the engine, not the model)
    valid: bool = True
    validation_error: Optional[str] = None

    def sanity_check(self) -> "InferenceResult":
        from .palettes import is_valid_flow
        errs = []
        if self.flow_result not in PALETTES:
            errs.append(f"flow_result '{self.flow_result}' not one of the 10 palettes")
        if self.home_season not in HOME_SEASONS:
            errs.append(f"home_season '{self.home_season}' invalid")
        if self.flow_result in PALETTES and self.home_season in HOME_SEASONS \
                and not is_valid_flow(self.flow_result, self.home_season):
            errs.append(f"'{self.flow_result}' is not a valid flow of {self.home_season}")
        if errs:
            self.valid = False
            self.validation_error = "; ".join(errs)
        return self


class CaseResult(BaseModel):
    """One client's outcome in a batch: model verdict vs Carol's ground truth."""
    client_id: str
    test_id: Optional[int] = None
    model: str = ""
    carol_result: Optional[str] = None         # raw column-O text
    carol_primary: Optional[str] = None
    carol_accepted: list[str] = Field(default_factory=list)
    predicted: Optional[str] = None
    match: bool = False
    match_kind: Literal["exact", "boundary", "miss", "error", "no_ground_truth"] = "miss"
    confidence: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    result: Optional[InferenceResult] = None


class BatchSummary(BaseModel):
    model: str
    provider: str
    total: int
    scored: int
    exact: int
    boundary: int
    misses: int
    errors: int
    accuracy: float                # (exact + boundary) / scored
    exact_accuracy: float          # exact / scored
    confusion: dict[str, dict[str, int]] = Field(default_factory=dict)
    cases: list[CaseResult] = Field(default_factory=list)
