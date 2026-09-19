from pydantic import BaseModel, Field


class DerivedProfile(BaseModel):
    skin_tone_class: str | None = None
    skin_tone_ita: float | None = None
    skin_tone_confidence: float | None = None
    style_vector: list[float] | None = None
    profile_version: int = 1
    ready_for_tryon: bool = False
    preferences: dict[str, object] = Field(default_factory=dict)
