from uuid import UUID

from pydantic import BaseModel

from schemas.common.enums import FitVerdict


class FitFeedbackCreate(BaseModel):
    buy_click_id: UUID | None = None
    garment_id: UUID
    brand_id: UUID
    category: str
    fit_type: str | None = None
    size_label: str
    verdict: FitVerdict
