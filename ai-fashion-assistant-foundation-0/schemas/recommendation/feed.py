from uuid import UUID

from pydantic import BaseModel


class FeedItem(BaseModel):
    garment_id: UUID
    reasons: list[str] = []


class FeedResponse(BaseModel):
    feed_version: str
    items: list[FeedItem]
    next_cursor: str | None = None
