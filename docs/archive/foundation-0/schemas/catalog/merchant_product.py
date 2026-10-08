from uuid import UUID

from pydantic import BaseModel


class MerchantProduct(BaseModel):
    id: UUID
    merchant_id: UUID
    brand_id: UUID | None = None
    source_product_id: str
    title: str
    description: str | None = None
    source_url: str
