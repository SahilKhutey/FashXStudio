from typing import Generic, List, Optional, TypeVar
from pydantic import Field
from schemas.base import BaseContractModel

T = TypeVar("T")


class PaginationMetadata(BaseContractModel):
    limit: int = Field(default=20, ge=1, le=100)
    has_more: bool = False
    next_cursor: Optional[str] = None
    total_count: Optional[int] = None


class PaginatedResponse(BaseContractModel, Generic[T]):
    data: List[T]
    pagination: PaginationMetadata
