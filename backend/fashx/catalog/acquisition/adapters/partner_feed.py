"""Authorized partner feed adapter reading structured catalog feeds."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from fashx.catalog.acquisition.adapters.base import BaseSourceAdapter
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.registry import SourceConfig


class PartnerFeedAdapter(BaseSourceAdapter):
    """Adapter for authorized partner CSV and JSON feeds."""

    def __init__(
        self,
        config: SourceConfig | None = None,
        feed_items: Sequence[SourceProduct] | None = None,
        feed_csv_path: Path | None = None,
    ) -> None:
        cfg = config or SourceConfig(
            source_slug="partner-feed",
            name="Authorized Partner Feed",
            kind="feed_url",
            image_policy="mirror",
        )
        super().__init__(cfg)
        self._feed_items = list(feed_items) if feed_items is not None else None
        self._feed_csv_path = feed_csv_path

    def set_items(self, items: Sequence[SourceProduct]) -> None:
        self._feed_items = list(items)

    async def _fetch_batch_impl(
        self,
        cursor: str | None,
        limit: int,
    ) -> AcquisitionBatch:
        items: list[SourceProduct] = []

        if self._feed_items is not None:
            items = self._feed_items
        elif self._feed_csv_path and self._feed_csv_path.exists():
            with self._feed_csv_path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    sizes = tuple(s.strip() for s in r.get("size_values", "").split("|") if s.strip())
                    items.append(
                        SourceProduct(
                            source_slug=self.source_slug,
                            source_product_id=r["source_product_id"].strip(),
                            title=r["title"].strip(),
                            category=r["category"].strip(),
                            subcategory=r.get("subcategory", "").strip() or None,
                            brand=r.get("brand", "").strip() or None,
                            description=r.get("description", "").strip() or None,
                            price_minor=int(r["price_minor"].strip()),
                            currency=r.get("currency", "INR").strip(),
                            product_url=r.get("product_url", "").strip(),
                            image_url=r.get("image_url", "").strip() or None,
                            in_stock=r.get("in_stock", "true").strip().lower() in {"true", "1", "yes"},
                            sizes=sizes,
                            image_rights=r.get("image_rights", "partner_authorized").strip(),
                            tryon_rights=r.get("tryon_rights", "false").strip().lower() in {"true", "1", "yes"},
                        )
                    )

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
