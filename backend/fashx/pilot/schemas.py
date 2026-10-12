from datetime import datetime
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Likert = Annotated[int, Field(ge=1, le=5)]


class JoinPilotRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32, description="10-character pilot invite code")
    os: str | None = None
    app_version: str | None = None


class JoinPilotResponse(BaseModel):
    cohort: str
    channel: str
    joined_at: datetime


class PilotFeedbackRequest(BaseModel):
    kind: Literal["bug", "idea", "praise", "privacy"]
    message: Annotated[str, Field(min_length=1, max_length=2000)]
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("context")
    @classmethod
    def validate_context_keys(cls, v: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = {"screen", "app_version", "job_id"}
        return {k: str(val)[:128] for k, val in v.items() if k in allowed_keys}


class TryonFirst(BaseModel):
    model_config = ConfigDict(extra="forbid")
    looked_like_me: Likert
    trust_for_buying: Likert
    comment: Annotated[str, Field(max_length=500)] = ""


class FeedDay5(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relevance: Likert
    found_my_size: bool
    missing: Annotated[str, Field(max_length=500)] = ""


class EndOfPilot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sus: Annotated[list[Likert], Field(min_length=10, max_length=10)]
    disappointed: Literal["very", "somewhat", "not"]
    nps: Annotated[int, Field(ge=0, le=10)]
    photo_comfort: Likert
    would_use_weekly: Likert
    bought_any: bool
    bought_notes: Annotated[str, Field(max_length=500)] = ""
    best: Annotated[str, Field(max_length=500)] = ""
    worst: Annotated[str, Field(max_length=500)] = ""


class SubmitSurveyRequest(BaseModel):
    survey_key: Literal["tryon_first", "feed_day5", "end_of_pilot"]
    answers: dict[str, Any]


class PendingSurveyResponse(BaseModel):
    survey_key: Literal["tryon_first", "feed_day5", "end_of_pilot"] | None
    description: str | None = None
