from pydantic import BaseModel, Field

from schemas.common.enums import BuildType


class BodyProfile(BaseModel):
    height_cm: int | None = Field(default=None, ge=100, le=250)
    weight_kg: int | None = Field(default=None, ge=25, le=300)
    build: BuildType | None = None
