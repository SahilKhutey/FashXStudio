from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WardrobeItemType(str, Enum):
    PRODUCT = "PRODUCT"
    VTO_RESULT = "VTO_RESULT"


class SaveWardrobeItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_type: WardrobeItemType
    product_id: UUID | None = None
    offer_id: UUID | None = None
    tryon_job_id: UUID | None = None

    @model_validator(mode="after")
    def validate_item_type(self) -> SaveWardrobeItemRequest:
        if self.item_type == WardrobeItemType.PRODUCT:
            if not self.product_id or not self.offer_id:
                raise ValueError("PRODUCT_REQUIRES_PRODUCT_AND_OFFER")
            if self.tryon_job_id:
                raise ValueError("PRODUCT_CANNOT_REFERENCE_TRYON_JOB")
        if self.item_type == WardrobeItemType.VTO_RESULT:
            if not self.tryon_job_id:
                raise ValueError("VTO_RESULT_REQUIRES_JOB")
            if self.product_id or self.offer_id:
                raise ValueError("VTO_RESULT_CANNOT_REFERENCE_PRODUCT")
        return self


class CreateSavedLookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    item_ids: list[UUID] = Field(..., min_length=1, max_length=30)

    @field_validator("title")
    @classmethod
    def validate_title_non_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("LOOK_TITLE_EMPTY")
        return trimmed


class SavedLookSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    user_id: UUID
    title: str
    description: str | None = None
    item_ids: list[UUID]
    item_count: int
    created_at: datetime
    updated_at: datetime
