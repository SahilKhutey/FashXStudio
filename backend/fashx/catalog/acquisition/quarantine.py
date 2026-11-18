"""Durable record-level quarantine management for catalog ingestion."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_sync import CatalogIngestionQuarantine

logger = logging.getLogger(__name__)


class CatalogQuarantineService:
    """Manages persistent quarantine records for invalid, unmapped, or unauthorized product records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def quarantine_record(
        self,
        *,
        ingest_run_id: UUID,
        source_id: UUID,
        source_product_id: str | None,
        reason_code: str,
        field_name: str | None = None,
        raw_record: dict[str, Any] | None = None,
        status: str = "PENDING",
        resolution_note: str | None = None,
    ) -> CatalogIngestionQuarantine:
        """Idempotently insert or update a record in quarantine."""
        now = datetime.now(UTC)

        # Sanitize raw_record: strip credentials, access tokens, signed URLs, and large binary blobs
        safe_ref = self._sanitize_record_reference(raw_record) if raw_record else None
        record_hash = None
        if safe_ref:
            raw_str = str(sorted(safe_ref.items()))
            record_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

        # Check existing quarantine record by (source_id, source_product_id, reason_code)
        stmt = select(CatalogIngestionQuarantine).where(
            CatalogIngestionQuarantine.source_id == source_id,
            CatalogIngestionQuarantine.source_product_id == source_product_id,
            CatalogIngestionQuarantine.reason_code == reason_code,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.ingest_run_id = ingest_run_id
            existing.field_name = field_name
            existing.safe_record_reference = safe_ref
            existing.record_hash = record_hash
            existing.last_seen_at = now
            if resolution_note:
                existing.resolution_note = resolution_note
            return existing

        quarantine_entry = CatalogIngestionQuarantine(
            id=uuid4(),
            ingest_run_id=ingest_run_id,
            source_id=source_id,
            source_product_id=source_product_id,
            reason_code=reason_code,
            field_name=field_name,
            safe_record_reference=safe_ref,
            record_hash=record_hash,
            status=status,
            first_seen_at=now,
            last_seen_at=now,
            resolution_note=resolution_note,
        )
        self.session.add(quarantine_entry)
        return quarantine_entry

    async def list_quarantine(
        self,
        source_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CatalogIngestionQuarantine], int]:
        """List quarantined items with optional source and status filters."""
        query = select(CatalogIngestionQuarantine)
        count_query = select(func.count(CatalogIngestionQuarantine.id))

        if source_id:
            query = query.where(CatalogIngestionQuarantine.source_id == source_id)
            count_query = count_query.where(CatalogIngestionQuarantine.source_id == source_id)

        if status:
            query = query.where(CatalogIngestionQuarantine.status == status.upper())
            count_query = count_query.where(CatalogIngestionQuarantine.status == status.upper())

        query = (
            query.order_by(CatalogIngestionQuarantine.last_seen_at.desc())
            .limit(limit)
            .offset(offset)
        )

        total = (await self.session.execute(count_query)).scalar() or 0
        records = (await self.session.execute(query)).scalars().all()
        return list(records), total

    async def get_by_id(self, quarantine_id: UUID) -> CatalogIngestionQuarantine | None:
        """Retrieve a specific quarantine entry by ID."""
        stmt = select(CatalogIngestionQuarantine).where(
            CatalogIngestionQuarantine.id == quarantine_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def mark_reprocessed(
        self,
        quarantine_id: UUID,
        note: str = "Reprocessed successfully",
    ) -> CatalogIngestionQuarantine | None:
        """Mark a quarantine record as reprocessed."""
        record = await self.get_by_id(quarantine_id)
        if record:
            record.status = "REPROCESSED"
            record.resolved_at = datetime.now(UTC)
            record.resolution_note = note
        return record

    @staticmethod
    def _sanitize_record_reference(raw: dict[str, Any]) -> dict[str, Any]:
        """Strip sensitive credentials, authentication tokens, and oversized payload fields."""
        sanitized = {}
        sensitive_keys = {
            "token",
            "access_token",
            "secret",
            "password",
            "api_key",
            "credentials",
            "signature",
            "auth",
            "authorization",
        }
        for k, v in raw.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in sensitive_keys):
                sanitized[k] = "***REDACTED***"
            elif isinstance(v, (str, int, float, bool)) or v is None:
                # Truncate overly long text fields to avoid database bloat
                if isinstance(v, str) and len(v) > 2000:
                    sanitized[k] = v[:2000] + "...[TRUNCATED]"
                else:
                    sanitized[k] = v
            elif isinstance(v, (list, tuple)):
                sanitized[k] = [str(item)[:200] for item in v[:50]]
            elif isinstance(v, dict):
                sanitized[k] = {str(dk): str(dv)[:200] for dk, dv in list(v.items())[:20]}
        return sanitized
