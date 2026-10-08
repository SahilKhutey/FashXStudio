from uuid import UUID

from pydantic import BaseModel


class TryOnArtifact(BaseModel):
    id: UUID
    job_id: UUID
    artifact_key: str
    result_key: str
    model_version: str
    pipeline_version: str
    photo_version: int
    garment_version: int
