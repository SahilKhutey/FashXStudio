from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class AnalyticsWindow(BaseModel):
    start_at: datetime
    end_at: datetime


class ValidationMetrics(BaseModel):
    window: AnalyticsWindow
    users_created: int = Field(ge=0)
    tryon_started: int = Field(ge=0)
    tryon_completed: int = Field(ge=0)
    tryon_failed: int = Field(ge=0)
    tryon_viewed: int = Field(ge=0)
    tryon_retry_requested: int = Field(ge=0)
    tryon_feedback_submitted: int = Field(ge=0)
    wardrobe_saved: int = Field(ge=0)
    buy_clicks: int = Field(ge=0)
    unique_tryon_users: int = Field(ge=0)
    repeat_tryon_users: int = Field(ge=0)
    unique_session_users: int = Field(ge=0)
    repeat_session_users: int = Field(ge=0)
    tryon_completion_rate: float = Field(ge=0, le=1)
    result_view_rate: float = Field(ge=0, le=1)
    feedback_rate: float = Field(ge=0, le=1)
    save_rate: float = Field(ge=0, le=1)
    buy_click_rate: float = Field(ge=0, le=1)
    repeat_tryon_rate: float = Field(ge=0, le=1)
    repeat_session_rate: float = Field(ge=0, le=1)


class AnalyticsEventCreate(BaseModel):
    event_type: str = Field(pattern=r"^(session_started|session_ended)$")
    session_id: str = Field(min_length=8, max_length=128)
    screen_context: str | None = Field(default=None, max_length=64)


class AnalyticsEventResponse(BaseModel):
    accepted: bool = True
