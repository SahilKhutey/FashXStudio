from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class GarmentAttributes:
    silhouette: str | None = None
    collar: str | None = None
    sleeve_length: str | None = None
    pattern: str | None = None
    dominant_color: str | None = None
    secondary_color: str | None = None
    formality: str | None = None
    material: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class EnrichmentResult:
    attributes: GarmentAttributes
    confidence_summary: dict[str, float] = field(default_factory=dict)
    model_version: str = "heuristic-v1.0"
    embedding: list[float] | None = None


class GarmentEnricherPort(Protocol):
    """Abstract port for garment attribute extraction and multimodal enrichment."""

    async def enrich(
        self,
        title: str,
        description: str | None = None,
        image_bytes: bytes | None = None,
    ) -> EnrichmentResult:
        """Extract structured visual and semantic attributes from listing metadata and image."""
        ...
