"""Versioned public response contracts for API consumers."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Methodology(ContractModel):
    name: str
    version: str
    inputs: list[str]
    does_not_do: list[str]


class ImageAnalysis(ContractModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    aspect_ratio: float = Field(gt=0)
    composition: str
    lighting: str
    palette: str
    average_rgb: tuple[float, float, float]
    brightness: float = Field(ge=0, le=255)


class Provenance(ContractModel):
    status: Literal["valid", "invalid", "not_present", "unsupported", "not_checked"]
    claim_generator: str | None = None
    validation_errors: tuple[str, ...] = ()


class VisionContextResponse(ContractModel):
    description: str
    tags: tuple[str, ...]


class ReconstructionCandidate(ContractModel):
    model: str
    selection_rationale: str
    prompt: str
    negative_prompt: str | None = None
    parameters: dict[str, Any]


class HumanReview(ContractModel):
    required: bool
    reason: str


class AnalysisResponse(ContractModel):
    analysis_id: str
    methodology: Methodology
    analysis: ImageAnalysis
    provenance: Provenance
    vision_context: VisionContextResponse | None = None
    candidates: list[ReconstructionCandidate]
    human_review: HumanReview
    disclaimer: str


class HealthResponse(ContractModel):
    status: Literal["ok"]


class ReadinessResponse(ContractModel):
    status: Literal["ready"]
    environment: str
