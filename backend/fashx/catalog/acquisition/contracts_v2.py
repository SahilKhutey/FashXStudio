"""Source adapter contracts and data transfer objects for Phase 05.2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct


class SyncMode(StrEnum):
    FULL = "full"
    INCREMENTAL = "incremental"


class SourceHealthState(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    AUTH_FAILED = "auth_failed"
    STALE = "stale"
    DISABLED = "disabled"


class SourceErrorCode(StrEnum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMITED = "rate_limited"
    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    INVALID_REQUEST = "invalid_request"
    CURSOR_EXPIRED = "cursor_expired"
    SCHEMA_CHANGED = "schema_changed"
    PERMISSION_REVOKED = "permission_revoked"


class IntegrationStatus(StrEnum):
    MOCK = "MOCK"
    LOCAL = "LOCAL"
    SANDBOX_VERIFIED = "SANDBOX_VERIFIED"
    PRODUCTION_VERIFIED = "PRODUCTION_VERIFIED"


@dataclass(frozen=True)
class SourceCapabilities:
    """Declared capabilities of a catalog source integration."""

    full_sync: bool = True
    incremental_sync: bool = False
    conditional_requests: bool = False
    deletion_signals: bool = False
    supported_formats: tuple[str, ...] = ("json",)


@dataclass
class SourceHealthReport:
    """Health and operational telemetry for a catalog source."""

    source_slug: str
    state: SourceHealthState
    last_check_at: datetime | None = None
    last_successful_sync_at: datetime | None = None
    last_failed_sync_at: datetime | None = None
    consecutive_failures: int = 0
    latency_ms: float | None = None
    last_error_code: SourceErrorCode | None = None
    message: str = "Healthy"


@runtime_checkable
class CatalogSourceAdapterV2(Protocol):
    """Extended adapter protocol supporting production synchronization, health, and error mapping."""

    @property
    def source_slug(self) -> str: ...

    @property
    def integration_status(self) -> IntegrationStatus: ...

    def capabilities(self) -> SourceCapabilities: ...

    async def health_check(self) -> SourceHealthReport: ...

    async def fetch_page(
        self,
        cursor: str | None = None,
        limit: int = 100,
    ) -> AcquisitionBatch: ...

    async def start_full_sync(self) -> str: ...

    async def start_incremental_sync(
        self,
        watermark: datetime | None = None,
        cursor: str | None = None,
    ) -> str: ...

    def normalize_product(self, raw_record: dict[str, Any]) -> SourceProduct: ...

    def map_error(self, exc: Exception) -> SourceErrorCode: ...
