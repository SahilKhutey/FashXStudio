from uuid import UUID

from pydantic import BaseModel

from schemas.common.enums import DataType


class ConsentRecord(BaseModel):
    user_id: UUID
    data_type: DataType
    granted: bool
    updated_at: str


class ConsentUpdate(BaseModel):
    data_type: DataType
    granted: bool
