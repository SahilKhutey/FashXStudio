from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from database.models.catalog_embeddings import (
    EmbeddingMigrationRecord,
    EmbeddingModelRegistryRecord,
    ProductImageEmbeddingRecord,
)

logger = logging.getLogger(__name__)


class ModelMigrationError(Exception):
    """Raised when model version migration fails or violates invariants."""


class ModelMigrationManager:
    """Orchestrates blue/green model version migration, cutover, and rollback."""

    def start_migration(
        self,
        session: Session,
        source_model_id: str,
        source_model_version: str,
        target_model_id: str,
        target_model_version: str,
    ) -> EmbeddingMigrationRecord:
        """Initialize a model version migration record."""
        # Check target model exists in registry
        target_reg = session.scalars(
            select(EmbeddingModelRegistryRecord).where(
                EmbeddingModelRegistryRecord.model_id == target_model_id,
                EmbeddingModelRegistryRecord.model_version == target_model_version,
            )
        ).first()

        if target_reg is None:
            raise ModelMigrationError(
                f"Target model '{target_model_id}:{target_model_version}' is not registered in embedding_model_registry"
            )

        # Count total existing source records
        total_source = session.scalar(
            select(func.count(ProductImageEmbeddingRecord.id)).where(
                ProductImageEmbeddingRecord.model_id == source_model_id,
                ProductImageEmbeddingRecord.model_version == source_model_version,
            )
        ) or 0

        migration = EmbeddingMigrationRecord(
            source_model_id=source_model_id,
            source_model_version=source_model_version,
            target_model_id=target_model_id,
            target_model_version=target_model_version,
            migration_phase="DUAL_WRITE",
            total_records=total_source,
            migrated_records=0,
            status="IN_PROGRESS",
        )
        session.add(migration)
        session.flush()
        return migration

    def execute_cutover(
        self,
        session: Session,
        migration_id: UUID,
    ) -> EmbeddingMigrationRecord:
        """Perform atomic cutover: activate target model vectors and deactivate source vectors."""
        migration = session.get(EmbeddingMigrationRecord, migration_id)
        if migration is None:
            raise KeyError(f"Migration {migration_id} not found")

        if migration.status != "IN_PROGRESS":
            raise ModelMigrationError(
                f"Cannot cutover migration in status '{migration.status}': must be IN_PROGRESS"
            )

        # Deactivate source model records
        session.execute(
            update(ProductImageEmbeddingRecord)
            .where(
                ProductImageEmbeddingRecord.model_id == migration.source_model_id,
                ProductImageEmbeddingRecord.model_version == migration.source_model_version,
            )
            .values(is_active=False)
        )

        # Activate target model records
        session.execute(
            update(ProductImageEmbeddingRecord)
            .where(
                ProductImageEmbeddingRecord.model_id == migration.target_model_id,
                ProductImageEmbeddingRecord.model_version == migration.target_model_version,
            )
            .values(is_active=True)
        )

        migration.migration_phase = "CUTOVER"
        migration.status = "COMPLETED"
        migration.completed_at = datetime.now(UTC)
        session.flush()
        logger.info("Successfully executed cutover for migration %s", migration_id)
        return migration

    def rollback(
        self,
        session: Session,
        migration_id: UUID,
    ) -> EmbeddingMigrationRecord:
        """Rollback migration: restore source model vectors as active."""
        migration = session.get(EmbeddingMigrationRecord, migration_id)
        if migration is None:
            raise KeyError(f"Migration {migration_id} not found")

        # Deactivate target model records
        session.execute(
            update(ProductImageEmbeddingRecord)
            .where(
                ProductImageEmbeddingRecord.model_id == migration.target_model_id,
                ProductImageEmbeddingRecord.model_version == migration.target_model_version,
            )
            .values(is_active=False)
        )

        # Re-activate source model records
        session.execute(
            update(ProductImageEmbeddingRecord)
            .where(
                ProductImageEmbeddingRecord.model_id == migration.source_model_id,
                ProductImageEmbeddingRecord.model_version == migration.source_model_version,
            )
            .values(is_active=True)
        )

        migration.migration_phase = "ROLLBACK"
        migration.status = "ROLLED_BACK"
        migration.completed_at = datetime.now(UTC)
        session.flush()
        logger.warning("Rolled back migration %s", migration_id)
        return migration


__all__ = [
    "ModelMigrationError",
    "ModelMigrationManager",
]
