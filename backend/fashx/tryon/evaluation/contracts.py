"""Evaluation contracts, schemas, and data structures for Virtual Try-On quality benchmarks.

Strict Invariants:
1. Every evaluation pair MUST include traceable permission references.
2. Participant IDs are strictly pseudonymous; never expose real names, PII, or contact info.
3. Category support states strictly gate which garments are eligible for live inference.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluationDifficulty(str, Enum):
    STANDARD = "STANDARD"
    CHALLENGING = "CHALLENGING"
    NEGATIVE = "NEGATIVE"


class ExpectedOutcome(str, Enum):
    INFERENCE = "INFERENCE"
    REJECT_INPUT = "REJECT_INPUT"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class CategoryStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    EVALUATING = "EVALUATING"
    NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT"
    APPROVED_LIMITED = "APPROVED_LIMITED"
    BLOCKED = "BLOCKED"


class DatasetPartition(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION = "VALIDATION"
    HOLDOUT_TEST = "HOLDOUT_TEST"


def is_vto_category_allowed(status: str | CategoryStatus) -> bool:
    """Determine if a garment category status permits customer virtual try-on."""
    val = status.value if isinstance(status, CategoryStatus) else status
    return val == CategoryStatus.APPROVED_LIMITED.value


class EvaluationPair(BaseModel):
    """Immutable definition of an evaluation pair linking a shopper portrait to a garment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair_id: str = Field(..., description="Unique deterministic identifier for the pair")
    dataset_version: str = Field(..., description="Frozen dataset benchmark version")
    participant_id: str = Field(..., description="Pseudonymous participant ID")
    shopper_asset_id: UUID = Field(..., description="Shopper portrait asset reference")
    garment_asset_id: UUID = Field(..., description="Garment image asset reference")
    canonical_product_id: UUID = Field(..., description="Target catalog garment entity")
    garment_category: str = Field(..., description="Garment taxonomy category")
    market: str = Field(default="IN", description="Target geographical market code")
    partition: DatasetPartition = Field(
        default=DatasetPartition.DEVELOPMENT,
        description="Dataset split (DEVELOPMENT, VALIDATION, HOLDOUT_TEST)",
    )
    height_band: str | None = Field(default=None, description="Consented height range band")
    body_representation_group: str | None = Field(
        default=None, description="Consented build descriptor"
    )
    skin_tone_annotation: str | None = Field(
        default=None, description="Consented skin-tone annotation"
    )
    lighting: str = Field(default="NATURAL_BRIGHT", description="Lighting condition classification")
    camera_distance: str = Field(default="FULL_BODY", description="Framing distance")
    pose: str = Field(default="FRONT_RELAXED", description="Pose orientation")
    difficulty: EvaluationDifficulty = Field(
        default=EvaluationDifficulty.STANDARD, description="Case difficulty"
    )
    permission_record_id: str = Field(..., description="Audited permission record ID")
    eligible_for_live_provider: bool = Field(
        default=True, description="Whether pair is cleared for live inference"
    )
    expected_outcome: ExpectedOutcome = Field(
        default=ExpectedOutcome.INFERENCE, description="Expected pipeline outcome"
    )


class EvaluationRunConfig(BaseModel):
    """Immutable snapshot of the inference provider and application configuration for a run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evaluation_run_id: str = Field(..., description="Unique run identifier")
    provider: str = Field(..., description="Provider adapter key (e.g. fashn)")
    model: str = Field(..., description="Model family identifier")
    model_version: str = Field(
        default="NOT_EXPOSED", description="Specific model version or NOT_EXPOSED"
    )
    provider_api_version: str = Field(default="v1", description="Provider API version")
    configuration_version: str = Field(..., description="Application rendering config revision")
    preprocessing_version: str = Field(..., description="Image preprocessing pipeline version")
    policy_version: str = Field(..., description="Input validation & safety policy revision")
    prompt_version: str = Field(default="default", description="Prompt template version")
    spending_ceiling_usd: float = Field(
        default=50.0, ge=0.0, description="Spending limit allocated for this evaluation run"
    )
    git_commit_sha: str | None = Field(default=None, description="Git commit hash of running code")
    started_at: datetime = Field(..., description="Run initialization timestamp")


def load_manifest_pairs(manifest_path: str | Path) -> list[EvaluationPair]:
    """Parse and validate evaluation pairs from a JSONL manifest file."""
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation manifest file not found: {path}")

    pairs: list[EvaluationPair] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                data = json.loads(line)
                pairs.append(EvaluationPair(**data))
            except Exception as e:
                raise ValueError(f"Invalid manifest line {line_no} in {path.name}: {e}") from e

    return pairs
