from uuid import UUID

from pydantic import BaseModel, Field


class TryOnResultMetadata(BaseModel):
    artifact_id: UUID | None = None
    quality_status: str
    quality_score: float | None = None
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
    content_type: str | None = None
    content_sha256: str | None = None
    quality_reasons: list[str] = Field(default_factory=list)
    result_url: str | None = None
