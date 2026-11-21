"""Authorized HTTP feed adapter connecting to approved merchant HTTPS feeds."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from fashx.catalog.acquisition.adapters.base import BaseSourceAdapter
from fashx.catalog.acquisition.auth import NoAuthProvider, SourceAuthProvider
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.contracts_v2 import (
    CatalogSourceAdapterV2,
    IntegrationStatus,
    SourceCapabilities,
    SourceErrorCode,
    SourceHealthReport,
    SourceHealthState,
)
from fashx.catalog.acquisition.errors import SchemaChangedError, map_provider_error
from fashx.catalog.acquisition.http_client import SourceHttpClient
from fashx.catalog.acquisition.registry import SourceConfig

logger = logging.getLogger(__name__)


class AuthorizedHttpFeedAdapter(BaseSourceAdapter, CatalogSourceAdapterV2):
    """Adapter for authorized external merchant feeds over HTTPS with SSRF safeguards."""

    def __init__(
        self,
        config: SourceConfig,
        feed_url: str,
        auth_provider: SourceAuthProvider | None = None,
        allowed_hostnames: Sequence[str] = (),
        http_client: SourceHttpClient | None = None,
        integration_status: IntegrationStatus = IntegrationStatus.LOCAL,
    ) -> None:
        super().__init__(config)
        self.feed_url = feed_url
        self.auth_provider = auth_provider or NoAuthProvider()
        self.allowed_hostnames = allowed_hostnames
        self._integration_status = integration_status
        self.http_client = http_client or SourceHttpClient(
            allowed_hostnames=self.allowed_hostnames,
            require_https=True,
        )
        self._etag: str | None = None
        self._last_modified: str | None = None

    @property
    def integration_status(self) -> IntegrationStatus:
        return self._integration_status

    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            full_sync=True,
            incremental_sync=True,
            conditional_requests=True,
            deletion_signals=False,
            supported_formats=("json", "csv"),
        )

    def normalize_product(self, raw: dict[str, Any]) -> SourceProduct:
        """Map feed schema fields to canonical SourceProduct."""
        if not raw.get("source_product_id") or not raw.get("title"):
            raise SchemaChangedError("Feed product missing required 'source_product_id' or 'title'")

        sizes = tuple(raw.get("sizes", [])) if isinstance(raw.get("sizes"), list) else ()
        return SourceProduct(
            source_slug=self.source_slug,
            source_product_id=str(raw["source_product_id"]),
            title=str(raw["title"]),
            category=str(raw.get("category", "apparel")),
            price_minor=int(raw.get("price_minor", 0)),
            currency=str(raw.get("currency", "INR")),
            product_url=str(raw.get("product_url", "")),
            brand=raw.get("brand"),
            subcategory=raw.get("subcategory"),
            description=raw.get("description"),
            image_url=raw.get("image_url"),
            in_stock=bool(raw.get("in_stock", True)),
            sizes=sizes,
            source_updated_at=raw.get("source_updated_at"),
            raw_attributes=raw,
        )

    async def _fetch_batch_impl(
        self,
        cursor: str | None,
        limit: int,
    ) -> AcquisitionBatch:
        return await self.fetch_page(cursor=cursor, limit=limit)

    async def fetch_page(
        self,
        cursor: str | None = None,
        limit: int = 100,
    ) -> AcquisitionBatch:
        """Fetch a single page from the remote feed."""
        auth_material = await self.auth_provider.get_auth_material(self.source_slug)
        url = self.feed_url
        if cursor:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}cursor={cursor}&limit={limit}"

        try:
            data, resp = await self.http_client.get_json(
                url=url,
                headers=auth_material.headers,
                etag=self._etag,
                last_modified=self._last_modified,
            )

            # 304 Not Modified
            if resp.status_code == 304:
                return AcquisitionBatch(
                    source_slug=self.source_slug,
                    products=[],
                    cursor=None,
                    has_more=False,
                )

            # Update cache validation headers
            if "etag" in resp.headers:
                self._etag = resp.headers["etag"]
            if "last-modified" in resp.headers:
                self._last_modified = resp.headers["last-modified"]

            if not data or "products" not in data or not isinstance(data["products"], list):
                raise SchemaChangedError("Feed JSON missing 'products' list array.")

            raw_products = data["products"]
            normalized = [self.normalize_product(p) for p in raw_products]
            next_cursor = data.get("next_cursor")
            has_more = bool(next_cursor)

            return AcquisitionBatch(
                source_slug=self.source_slug,
                products=normalized,
                cursor=next_cursor,
                has_more=has_more,
                total_found=data.get("total_count", len(normalized)),
            )
        except Exception:
            self._record_failure()
            raise

    async def start_full_sync(self) -> str:
        self._etag = None
        self._last_modified = None
        return "full_sync_initialized"

    async def start_incremental_sync(
        self,
        watermark: Any = None,
        cursor: str | None = None,
    ) -> str:
        return f"incremental_sync_initialized:{cursor}"

    async def health_check(self) -> SourceHealthReport:
        """Check source connectivity via HEAD or lightweight probe."""
        try:
            auth_material = await self.auth_provider.get_auth_material(self.source_slug)
            resp = await self.http_client.get_response(
                url=self.feed_url,
                headers=auth_material.headers,
                etag=self._etag,
            )
            is_healthy = resp.status_code in (200, 304)
            state = SourceHealthState.HEALTHY if is_healthy else SourceHealthState.DEGRADED
            return SourceHealthReport(
                source_slug=self.source_slug,
                state=state,
                message="Remote feed accessible",
            )
        except Exception as exc:
            return SourceHealthReport(
                source_slug=self.source_slug,
                state=SourceHealthState.DEGRADED,
                last_error_code=self.map_error(exc),
                message=str(exc),
            )

    async def close(self) -> None:
        """Close underlying HTTP client connections."""
        if hasattr(self.http_client, "close"):
            await self.http_client.close()

    def map_error(self, exc: Exception) -> SourceErrorCode:
        return map_provider_error(exc)
