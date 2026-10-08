from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    height_cm: int | None = Field(default=None, ge=100, le=250)
    weight_kg: int | None = Field(default=None, ge=25, le=300)


class UserRef(BaseModel):
    user_id: UUID
