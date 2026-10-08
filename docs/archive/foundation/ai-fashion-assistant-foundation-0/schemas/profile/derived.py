from pydantic import BaseModel, Field


class DerivedProfile(BaseModel):
    skin_tone_class: str | None = None
    style_vector: list[float] | None = None
    preferences: dict[str, object] = Field(default_factory=dict)
