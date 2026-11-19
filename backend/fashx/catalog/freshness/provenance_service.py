"""Catalog provenance service for tracking attribute changes and source attribution."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_freshness import CatalogProvenanceRecord, ProvenanceEntityType


class CatalogProvenanceService:
    """Manages historical attribute attribution and source provenance."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_attribute_change(
        self,
        entity_type: ProvenanceEntityType | str,
        entity_id: UUID,
        attribute_name: str,
        attribute_value: Any,
        source_id: UUID,
        merchant_id: UUID | None = None,
        ingest_run_id: UUID | None = None,
        confidence: float = 1.0,
        source_updated_at: datetime | None = None,
    ) -> CatalogProvenanceRecord:
        """Persist an attribute observation with source and run provenance."""
        val_str = (
            json.dumps(attribute_value)
            if isinstance(attribute_value, (dict, list))
            else str(attribute_value)
            if attribute_value is not None
            else None
        )

        record = CatalogProvenanceRecord(
            entity_type=str(entity_type),
            entity_id=entity_id,
            attribute_name=attribute_name,
            attribute_value=val_str,
            source_id=source_id,
            merchant_id=merchant_id,
            ingest_run_id=ingest_run_id,
            confidence=confidence,
            source_updated_at=source_updated_at,
            recorded_at=datetime.now(UTC),
        )
        self.session.add(record)
        return record

    async def get_provenance_history(
        self,
        entity_type: ProvenanceEntityType | str,
        entity_id: UUID,
        attribute_name: str | None = None,
    ) -> list[CatalogProvenanceRecord]:
        """Fetch historical provenance observations for an entity."""
        stmt = select(CatalogProvenanceRecord).where(
            CatalogProvenanceRecord.entity_type == str(entity_type),
            CatalogProvenanceRecord.entity_id == entity_id,
        )
        if attribute_name:
            stmt = stmt.where(CatalogProvenanceRecord.attribute_name == attribute_name)
        stmt = stmt.order_by(CatalogProvenanceRecord.recorded_at.desc())
        result = await self.session.scalars(stmt)
        return list(result.all())
