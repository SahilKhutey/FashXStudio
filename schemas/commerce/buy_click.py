from uuid import UUID

from pydantic import BaseModel


class BuyClickCreate(BaseModel):
    garment_id: UUID
    offer_id: UUID


class BuyClickResponse(BaseModel):
    buy_click_id: UUID
    redirect_url: str
