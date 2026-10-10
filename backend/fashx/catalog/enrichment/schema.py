"""Controlled schema for visual attribute extraction and VLM enrichment."""

from typing import Literal

from pydantic import BaseModel, Field


class GarmentAttrs(BaseModel):
    """Structured visual and semantic attributes extracted by Vision-Language Models."""

    category: Literal[
        "top", "bottom", "one_piece", "outerwear", "footwear", "accessory", "other"
    ]
    sub_category: str
    primary_color: str
    secondary_colors: list[str] = Field(default_factory=list)
    pattern: Literal[
        "solid", "striped", "checked", "floral", "printed", "embroidered", "other"
    ]
    neckline: str | None = None
    sleeve_length: Literal["sleeveless", "short", "three_quarter", "full"] | None = None
    length: Literal["crop", "regular", "knee", "midi", "maxi", "ankle"] | None = None
    fit: Literal["slim", "regular", "relaxed", "oversized"] | None = None
    ethnic_wear: bool
    ethnic_type: str | None = None  # saree, kurta, lehenga, salwar_set, sherwani, nehru_jacket, etc.
    formality: int = Field(ge=1, le=5)  # 1 = ultra casual, 5 = black-tie / bridal
    occasions: list[str] = Field(default_factory=list)
    seasons: list[str] = Field(default_factory=list)
    photo_type: Literal["flat_lay", "ghost_mannequin", "on_model", "other"]
    tryon_suitable: bool
    tryon_reason: str
    confidence: dict[str, float] = Field(default_factory=dict)
