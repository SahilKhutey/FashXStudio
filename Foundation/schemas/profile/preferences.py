from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    colors_favored: list[str] = Field(default_factory=list)
    colors_avoided: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)


class UserPreferencesUpdate(UserPreferences):
    pass
