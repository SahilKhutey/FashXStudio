"""Image takedown management, asset suspension, and cascade deletion workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import GarmentImage
from database.models.catalog_image import (
    CatalogImageAsset,
    CatalogImageDeletionJob,
    CatalogImageTakedown,
    CatalogImageTransformation,
    ImageAssetStatus,
    ImageDeletionJobStatus,
    ImageDeletionTargetType,
    ImageTakedownScope,
    ImageTakedownStatus,
)
from fashx.catalog.images.storage_service import ImageStorageService


class ImageLifecycleService:
    """Coordinates takedown enforcement, object deletion, and lifecycle transitions."""

    def __init__(self, session: AsyncSession, storage_service: ImageStorageService) -> None:
        self.session = session
        self.storage = storage_service

    async def initiate_takedown(
        self,
        reason_code: str,
        scope_type: ImageTakedownScope | str = ImageTakedownScope.SOURCE,
        source_id: UUID | None = None,
        merchant_id: UUID | None = None,
        scope_target: str | None = None,
        asset_id: UUID | None = None,
        audit_metadata: dict[str, Any] | None = None,
    ) -> CatalogImageTakedown:
        """Create takedown record, immediately suspend affected assets, and schedule deletion jobs."""
        now = datetime.now(UTC)
        takedown = CatalogImageTakedown(
            source_id=source_id,
            merchant_id=merchant_id,
            scope_type=scope_type.value if hasattr(scope_type, "value") else str(scope_type),
            scope_target=scope_target or (str(asset_id) if asset_id else None),
            reason_code=reason_code,
            status=ImageTakedownStatus.RECEIVED.value,
            audit_metadata=audit_metadata or {},
            received_at=now,
        )
        self.session.add(takedown)
        await self.session.flush()

        # 1. Immediately suspend affected assets
        query = select(CatalogImageAsset)
        if asset_id:
            query = query.where(CatalogImageAsset.id == asset_id)
        elif source_id:
            query = query.where(CatalogImageAsset.source_id == source_id)
        elif merchant_id:
            query = query.where(CatalogImageAsset.merchant_id == merchant_id)

        affected_assets = (await self.session.scalars(query)).all()

        for asset in affected_assets:
            asset.status = ImageAssetStatus.SUSPENDED.value
            asset.updated_at = now

            # Enqueue deletion job for original if present
            if asset.original_storage_key:
                del_orig = CatalogImageDeletionJob(
                    takedown_id=takedown.id,
                    asset_id=asset.id,
                    storage_key=asset.original_storage_key,
                    target_type=ImageDeletionTargetType.ORIGINAL.value,
                    status=ImageDeletionJobStatus.PENDING.value,
                )
                self.session.add(del_orig)

            # Enqueue deletion jobs for all transformations
            trans_query = select(CatalogImageTransformation).where(
                CatalogImageTransformation.asset_id == asset.id
            )
            transformations = (await self.session.scalars(trans_query)).all()
            for trans in transformations:
                trans.status = "SUSPENDED"
                del_trans = CatalogImageDeletionJob(
                    takedown_id=takedown.id,
                    asset_id=asset.id,
                    storage_key=trans.storage_key,
                    target_type=trans.transformation_type,
                    status=ImageDeletionJobStatus.PENDING.value,
                )
                self.session.add(del_trans)

        takedown.status = ImageTakedownStatus.SUSPENDED.value
        await self.session.flush()
        return takedown

    async def execute_deletion_jobs(self, takedown_id: UUID) -> tuple[int, int]:
        """Execute physical object storage deletions for a takedown.

        Returns (completed_count, failed_count).
        """
        now = datetime.now(UTC)
        query = select(CatalogImageDeletionJob).where(
            CatalogImageDeletionJob.takedown_id == takedown_id,
            CatalogImageDeletionJob.status == ImageDeletionJobStatus.PENDING.value,
        )
        jobs = (await self.session.scalars(query)).all()

        completed = 0
        failed = 0

        for job in jobs:
            job.attempt_count += 1
            success = await self.storage.delete(job.storage_key)
            if success:
                job.status = ImageDeletionJobStatus.COMPLETED.value
                job.confirmed_at = now
                completed += 1
            else:
                job.status = ImageDeletionJobStatus.FAILED.value
                job.error_message = "Storage delete operation failed"
                failed += 1

        # Check takedown completion
        takedown = await self.session.get(CatalogImageTakedown, takedown_id)
        if takedown:
            if failed == 0:
                takedown.status = ImageTakedownStatus.COMPLETED.value
                takedown.completed_at = now
            else:
                takedown.status = ImageTakedownStatus.PROCESSING.value

        # Update asset statuses to DELETED if all jobs completed
        if failed == 0 and takedown:
            asset_subquery = (
                select(CatalogImageDeletionJob.asset_id)
                .where(CatalogImageDeletionJob.takedown_id == takedown_id)
                .distinct()
            )
            asset_ids = (await self.session.scalars(asset_subquery)).all()
            for a_id in asset_ids:
                if a_id:
                    asset = await self.session.get(CatalogImageAsset, a_id)
                    if asset:
                        asset.status = ImageAssetStatus.DELETED.value
                        asset.deleted_at = now

                    # Deactivate or remove associated GarmentImage
                    stmt = (
                        update(GarmentImage)
                        .where(GarmentImage.asset_id == a_id)
                        .values(image_type="archived")
                    )
                    await self.session.execute(stmt)

        await self.session.flush()
        return completed, failed
