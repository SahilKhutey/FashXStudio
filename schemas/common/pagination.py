from typing import Generic, TypeVar

from pydantic import Field

from schemas.base import BaseContractModel

T = TypeVar("T")


class PaginationMetadata(BaseContractModel):
    limit: int = Field(default=20, ge=1, le=100)
    has_more: bool = False
    next_cursor: str | None = None
    total_count: int | None = None


class PaginatedResponse(BaseContractModel, Generic[T]):
    data: list[T]
    pagination: PaginationMetadata
