from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.identity.user import UserCreate
from schemas.profile.body import BodyProfile
from schemas.profile.preferences import UserPreferences


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    created_at: datetime
    body: BodyProfile
    preferences: UserPreferences


class ProfileCreateRequest(UserCreate):
    build: str | None = None
    colors_favored: list[str] = Field(default_factory=list)
    colors_avoided: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
