"""Amazon catalog source adapter implementing the common CatalogSourceAdapter protocol."""

from __future__ import annotations

from collections.abc import Sequence

from fashx.catalog.acquisition.adapters.base import BaseSourceAdapter
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.registry import SourceConfig


class AmazonAdapter(BaseSourceAdapter):
    """Adapter for authorized Amazon product feeds and Product Advertising API."""

    def __init__(
        self,
        config: SourceConfig | None = None,
        feed_items: Sequence[SourceProduct] | None = None,
    ) -> None:
        cfg = config or SourceConfig(
            source_slug="amazon",
            name="Amazon",
            kind="api",
            image_policy="mirror",
            max_rps=1.0,
            refresh_hours=12,
        )
        super().__init__(cfg)
        self._feed_items = list(feed_items) if feed_items is not None else None

    def set_items(self, items: Sequence[SourceProduct]) -> None:
        self._feed_items = list(items)

    async def _fetch_batch_impl(
        self,
        cursor: str | None,
        limit: int,
    ) -> AcquisitionBatch:
        items = self._feed_items if self._feed_items is not None else []
        offset = int(cursor) if cursor and cursor.isdigit() else 0
        paginated = items[offset : offset + limit]
        has_more = (offset + len(paginated)) < len(items)
        next_cursor = str(offset + limit) if has_more else None

        return AcquisitionBatch(
            source_slug=self.source_slug,
            products=paginated,
            cursor=next_cursor,
            has_more=has_more,
            total_found=len(items),
        )
