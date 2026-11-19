from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogPermissionStatus,
    CatalogSourcePermission,
)
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import ImagePermissionMatrixResponse


class ImagePermissionStatusService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_image_permission_matrix(
        self,
        source_id: UUID,
        merchant_id: UUID | None = None,
    ) -> ImagePermissionMatrixResponse:
        source = await self.session.get(CatalogSource, source_id)
        if not source:
            raise CatalogAuthorizationError(
                f"Catalog source '{source_id}' not found.",
                code="source_not_found",
            )
        if merchant_id and source.merchant_id != merchant_id:
            raise CatalogAuthorizationError(
                f"Access denied: source does not belong to merchant '{merchant_id}'.",
                code="tenant_isolation_violation",
            )

        # Query active granted permissions for this source
        perms_query = select(CatalogSourcePermission).where(
            CatalogSourcePermission.source_id == source_id,
            CatalogSourcePermission.permission_status == CatalogPermissionStatus.GRANTED.value,
        )
        perms_result = await self.session.execute(perms_query)
        active_codes = {p.permission_code for p in perms_result.scalars().all()}

        # Evaluate permissions with fallback to source boolean flags
        fetch_permitted = (
            CatalogPermissionCode.IMAGE_FETCH.value in active_codes
            or source.status == "cleared"
            or source.rights_display
        )
        store_permitted = (
            CatalogPermissionCode.IMAGE_STORE.value in active_codes
            or source.image_policy == "mirror"
        )
        display_permitted = (
            CatalogPermissionCode.IMAGE_DISPLAY.value in active_codes or source.rights_display
        )
        ai_processing_permitted = CatalogPermissionCode.IMAGE_AI_PROCESS.value in active_codes or (
            source.rights_tryon and CatalogPermissionCode.VTO_PROCESS.value in active_codes
        )
        vto_permitted = (
            CatalogPermissionCode.VTO_PROCESS.value in active_codes or source.rights_tryon
        )
        derivatives_retained = CatalogPermissionCode.DERIVATIVE_STORE.value in active_codes or (
            store_permitted and (display_permitted or vto_permitted)
        )

        # Asset counts from CatalogImageAsset
        total_assets = (
            await self.session.scalar(
                select(func.count())
                .select_from(CatalogImageAsset)
                .where(CatalogImageAsset.source_id == source_id)
            )
            or 0
        )

        active_assets = (
            await self.session.scalar(
                select(func.count())
                .select_from(CatalogImageAsset)
                .where(
                    CatalogImageAsset.source_id == source_id,
                    CatalogImageAsset.status == ImageAssetStatus.ACTIVE.value,
                )
            )
            or 0
        )

        suspended_assets = (
            await self.session.scalar(
                select(func.count())
                .select_from(CatalogImageAsset)
                .where(
                    CatalogImageAsset.source_id == source_id,
                    CatalogImageAsset.status == ImageAssetStatus.SUSPENDED.value,
                )
            )
            or 0
        )

        warnings: list[str] = []
        if not display_permitted:
            warnings.append(
                "Display permission not granted: product images will not appear on shopper-facing catalog."
            )
        if not vto_permitted:
            warnings.append(
                "VTO permission not granted: virtual try-on is disabled for garments from this source."
            )
        if not ai_processing_permitted:
            warnings.append(
                "AI processing permission not granted: image segmentation and feature extraction disabled."
            )
        if not store_permitted and source.image_policy == "mirror":
            warnings.append(
                "Mirror storage requested by policy but image storage permission is not granted."
            )

        return ImagePermissionMatrixResponse(
            source_id=source.id,
            merchant_id=source.merchant_id or source_id,
            fetch_permitted=fetch_permitted,
            store_permitted=store_permitted,
            display_permitted=display_permitted,
            ai_processing_permitted=ai_processing_permitted,
            vto_permitted=vto_permitted,
            derivatives_retained=derivatives_retained,
            total_assets_count=total_assets,
            active_assets_count=active_assets,
            suspended_assets_count=suspended_assets,
            warning_messages=warnings,
        )
