from uuid import UUID

from pydantic import BaseModel


class Brand(BaseModel):
    id: UUID
    name: str
    normalized_name: str
