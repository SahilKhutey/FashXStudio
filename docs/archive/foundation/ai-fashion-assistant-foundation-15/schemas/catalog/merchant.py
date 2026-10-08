from uuid import UUID

from pydantic import BaseModel


class Merchant(BaseModel):
    id: UUID
    name: str
    merchant_type: str
