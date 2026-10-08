from __future__ import annotations

from uuid import UUID

from api.app.feed.domain.ranking import feed_reasons
from api.app.feed.repositories.feed import FeedRepository
from schemas.catalog.search import CatalogItemSummary
from schemas.feed.api import FeedItem, FeedQuery, FeedResponse
from schemas.feed.cursor import decode_feed_cursor, encode_feed_cursor


class FeedApplicationService:
    def __init__(self, repository: FeedRepository) -> None:
        self.repository = repository

    async def get_feed(self, *, user_id: UUID, query: FeedQuery) -> FeedResponse:
        if query.price_min is not None and query.price_max is not None and query.price_min > query.price_max:
            raise ValueError("price_min cannot exceed price_max")

        cursor = decode_feed_cursor(query.cursor) if query.cursor else None
        rows = await self.repository.list_items(
            user_id=user_id,
            category=query.category,
            subcategory=query.subcategory,
            price_min=query.price_min,
            price_max=query.price_max,
            limit=query.limit + 1,
            cursor=cursor,
        )

        has_more = len(rows) > query.limit
        page = rows[: query.limit]
        items: list[FeedItem] = []
        for garment, lowest_price, primary_image, in_stock in page:
            summary = CatalogItemSummary(
                id=garment.id,
                display_name=garment.display_name,
                category=garment.category,
                subcategory=garment.subcategory,
                brand_id=garment.brand_id,
                version=garment.version,
                primary_image_key=primary_image,
                lowest_price_minor=lowest_price,
                currency="INR" if lowest_price is not None else None,
                in_stock=in_stock,
            )
            items.append(
                FeedItem(
                    product=summary,
                    reasons=feed_reasons(
                        category_filtered=query.category is not None,
                        price_filtered=query.price_min is not None or query.price_max is not None,
                    ),
                )
            )

        next_cursor = None
        if has_more and page:
            last = page[-1][0]
            next_cursor = encode_feed_cursor(created_at=last.created_at, garment_id=last.id)
        return FeedResponse(items=items, next_cursor=next_cursor)
