from typing import Dict, List
from pydantic import Field
from schemas.base import BaseContractModel


class RankingFeaturesV1(BaseContractModel):
    fit_compatibility_score: float = Field(ge=0.0, le=1.0)
    color_harmony_score: float = Field(ge=0.0, le=1.0)
    wardrobe_co_occurrence_score: float = Field(ge=0.0, le=1.0)
    user_preference_score: float = Field(ge=0.0, le=1.0)
    context_weather_score: float = Field(ge=0.0, le=1.0)
    total_score: float = Field(ge=0.0, le=1.0)
