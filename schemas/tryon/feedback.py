from datetime import datetime

from pydantic import Field

from schemas.base import BaseContractModel


class TryOnFeedbackV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    feedback_id: str
    job_id: str
    user_id: str
    rating: int = Field(ge=1, le=5)
    artifact_issues: list[str] = Field(default_factory=list)
    comment: str | None = None
    submitted_at: datetime
