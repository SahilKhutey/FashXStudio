from pydantic import BaseModel, Field


class StyleProfile(BaseModel):
    embedding: list[float] = Field(default_factory=list)
    model_version: str | None = None
    updated_at: str | None = None
