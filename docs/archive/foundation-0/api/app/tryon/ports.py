from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class InferenceInput:
    """Input payload delivered to the try-on model adapter."""

    job_id: UUID
    user_id: UUID
    garment_id: UUID
    user_photo_bytes: bytes
    garment_image_bytes: bytes
    garment_category: str
    garment_silhouette: str = "regular"
    render_config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InferenceOutput:
    """Result rendered by the try-on model adapter."""

    rendered_image_bytes: bytes
    model_version: str
    pipeline_version: str
    inference_latency_ms: float
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PostInferenceValidationResult:
    """Quality analysis of rendered try-on image."""

    is_acceptable: bool
    structural_score: float  # [0.0, 1.0]
    contrast_score: float  # Standard deviation of luminance
    mean_luminance: float  # [0, 255]
    failure_reason: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


class TryOnModelAdapterPort(Protocol):
    """Protocol for pluggable Virtual Try-On rendering adapters."""

    @property
    def model_version(self) -> str:
        """Name and version identifier of the underlying model."""
        ...

    @property
    def pipeline_version(self) -> str:
        """Version identifier of the preprocessing/rendering pipeline."""
        ...

    @property
    def is_commercial_cleared(self) -> bool:
        """Whether this model is legally authorized for commercial production usage."""
        ...

    async def execute_tryon(self, payload: InferenceInput) -> InferenceOutput:
        """Execute try-on inference and return rendered image bytes."""
        ...
