"""Orchestration pipeline for merchant product image acquisition, validation, storage, and transformation."""

from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import GarmentImage
from database.models.catalog_image import (
    CatalogImageAsset,
    CatalogImageTransformation,
    ImageAssetStatus,
)
from fashx.catalog.images.fetcher import ImageFetchError, SafeImageFetcher
from fashx.catalog.images.inspector import ImageInspectionError, ImageInspector
from fashx.catalog.images.models import (
    ImageJobRequest,
    ImageJobResult,
    ImageOperation,
    QualityScore,
    TransformationType,
)
from fashx.catalog.images.permissions import ImagePermissionService
from fashx.catalog.images.quality import ImageQualityValidator
from fashx.catalog.images.storage_service import ImageStorageService
from fashx.catalog.images.transformations import ImageTransformationService

logger = logging.getLogger(__name__)


class ProductImagePipeline:
    """End-to-end, permission-aware image pipeline ensuring reproducible assets and strict rights compliance."""

    def __init__(
        self,
        session: AsyncSession,
        storage_service: ImageStorageService,
        fetcher: SafeImageFetcher | None = None,
        permission_service: ImagePermissionService | None = None,
    ) -> None:
        self.session = session
        self.storage = storage_service
        self.fetcher = fetcher or SafeImageFetcher()
        self.permissions = permission_service or ImagePermissionService(session)

    async def process_image(self, request: ImageJobRequest) -> ImageJobResult:
        """Execute full image pipeline for an authorized product image."""
        result = ImageJobResult(success=False)

        # Step 1: Preflight Permission Check (Fail-closed before network access)
        fetch_perm = await self.permissions.evaluate(
            source_id=request.source_id,
            operation=ImageOperation.FETCH,
            category=request.category,
            correlation_id=request.correlation_id,
        )
        if not fetch_perm.allowed:
            result.error_code = "permission_denied_fetch"
            result.error_message = fetch_perm.reason or "IMAGE_FETCH permission denied"
            return result

        # Check subsequent rights
        store_perm = await self.permissions.evaluate(
            source_id=request.source_id,
            operation=ImageOperation.STORE,
            category=request.category,
            correlation_id=request.correlation_id,
        )
        display_perm = await self.permissions.evaluate(
            source_id=request.source_id,
            operation=ImageOperation.DISPLAY,
            category=request.category,
            correlation_id=request.correlation_id,
        )
        ai_perm = await self.permissions.evaluate(
            source_id=request.source_id,
            operation=ImageOperation.AI_PROCESS,
            category=request.category,
            correlation_id=request.correlation_id,
        )
        vto_perm = await self.permissions.evaluate(
            source_id=request.source_id,
            operation=ImageOperation.VTO,
            category=request.category,
            correlation_id=request.correlation_id,
        )

        # Step 2: Retrieve Image via Safe Fetcher
        try:
            raw_bytes, _content_type = await self.fetcher.fetch_bytes(request.image_url)
        except ImageFetchError as f_err:
            result.error_code = f_err.code
            result.error_message = f_err.message
            return result
        except Exception as exc:
            result.error_code = "fetch_failed"
            result.error_message = str(exc)
            return result

        # Step 3: Deep Byte Inspection & Format Verification
        try:
            inspected = ImageInspector.inspect(raw_bytes)
        except ImageInspectionError as i_err:
            result.error_code = i_err.code
            result.error_message = i_err.message
            return result
        except Exception as exc:
            result.error_code = "inspection_failed"
            result.error_message = str(exc)
            return result

        # Step 4: Quality Profile Evaluation
        disp_quality = ImageQualityValidator.evaluate_display_profile(inspected)
        vto_quality = ImageQualityValidator.evaluate_vto_profile(
            inspected, vto_permitted=(ai_perm.allowed and vto_perm.allowed)
        )
        quality_notes = {
            **disp_quality.notes,
            "vto_quality_score": vto_quality.score.value,
            "vto_quality_notes": vto_quality.notes,
        }

        if not disp_quality.passed:
            result.error_code = "quality_rejected"
            result.error_message = disp_quality.notes.get(
                "reason", "Image quality failed display checks"
            )
            return result

        quality_score = (
            QualityScore.PASS.value if disp_quality.passed else QualityScore.REVIEW.value
        )
        result.quality_score = quality_score

        # Step 5: Duplicate Detection (IMG-025, IMG-026)
        existing_stmt = select(CatalogImageAsset).where(
            CatalogImageAsset.source_id == request.source_id,
            CatalogImageAsset.original_sha256 == inspected.original_sha256,
        )
        existing_asset = (await self.session.scalars(existing_stmt)).first()

        created_keys: list[str] = []
        try:
            if (
                existing_asset is not None
                and existing_asset.source_product_id == request.source_product_id
            ):
                # Exact original duplicate for the same product -> reuse existing asset
                asset = existing_asset
                asset_id = asset.id
            else:
                asset_id = uuid4()
                original_key: str | None = None

                # Step 6: Store Original Bytes only if IMAGE_STORE is permitted
                if store_perm.allowed:
                    original_key = self.storage.format_original_key(
                        source_id=request.source_id,
                        asset_id=asset_id,
                        original_sha256=inspected.original_sha256,
                        extension=inspected.detected_format,
                    )
                    await self.storage.put(
                        original_key, raw_bytes, content_type=inspected.mime_type
                    )
                    created_keys.append(original_key)

                asset = CatalogImageAsset(
                    id=asset_id,
                    source_id=request.source_id,
                    merchant_id=request.merchant_id,
                    source_product_id=request.source_product_id,
                    source_variant_id=request.source_variant_id,
                    source_reference=request.image_url,
                    source_reference_hash=inspected.original_sha256,
                    original_storage_key=original_key,
                    original_sha256=inspected.original_sha256,
                    normalized_sha256=inspected.normalized_sha256,
                    perceptual_hash=inspected.perceptual_hash,
                    original_mime_type=inspected.mime_type,
                    original_width=inspected.width,
                    original_height=inspected.height,
                    original_bytes=inspected.byte_size,
                    permission_evidence_id=store_perm.evidence_id,
                    permission_revision=store_perm.revision,
                    permission_policy_version=store_perm.policy_version,
                    status=ImageAssetStatus.ACTIVE.value,
                    quality_score=quality_score,
                    quality_notes=quality_notes,
                )
                self.session.add(asset)
                await self.session.flush()

            # Step 7: Generate & Store Display Derivatives (if display_perm.allowed)
            transform_names: list[str] = []
            primary_display_key: str | None = None
            primary_display_hash: str | None = None

            if display_perm.allowed:
                for t_type in (
                    TransformationType.DISPLAY_THUMBNAIL,
                    TransformationType.DISPLAY_CARD,
                    TransformationType.DISPLAY_DETAIL,
                ):
                    deriv = ImageTransformationService.generate_display_derivative(
                        inspected=inspected,
                        transformation_type=t_type,
                        version="v1",
                    )
                    d_key = self.storage.format_display_key(
                        source_id=request.source_id,
                        asset_id=asset.id,
                        transformation_type=t_type,
                        version="v1",
                    )
                    await self.storage.put(d_key, deriv.data, content_type=deriv.mime_type)
                    created_keys.append(d_key)

                    # Check if transformation already recorded
                    t_stmt = select(CatalogImageTransformation).where(
                        CatalogImageTransformation.asset_id == asset.id,
                        CatalogImageTransformation.transformation_type == t_type.value,
                        CatalogImageTransformation.transformation_version == "v1",
                    )
                    existing_t = (await self.session.scalars(t_stmt)).first()
                    if existing_t is None:
                        t_record = CatalogImageTransformation(
                            asset_id=asset.id,
                            transformation_type=t_type.value,
                            transformation_version="v1",
                            processor_name=deriv.processor_name,
                            processor_version=deriv.processor_version,
                            storage_key=d_key,
                            output_mime_type=deriv.mime_type,
                            output_width=deriv.width,
                            output_height=deriv.height,
                            output_bytes=deriv.byte_size,
                            output_sha256=deriv.sha256,
                            status="ACTIVE",
                        )
                        self.session.add(t_record)

                    transform_names.append(t_type.value)
                    if t_type == TransformationType.DISPLAY_CARD:
                        primary_display_key = d_key
                        primary_display_hash = deriv.sha256

            # Step 8: Generate & Store VTO Derivative (if AI & VTO rights permitted)
            if ai_perm.allowed and vto_perm.allowed:
                vto_deriv = ImageTransformationService.generate_vto_input(
                    inspected=inspected,
                    version="v1",
                )
                vto_key = self.storage.format_vto_key(
                    source_id=request.source_id,
                    asset_id=asset.id,
                    version="v1",
                )
                await self.storage.put(vto_key, vto_deriv.data, content_type=vto_deriv.mime_type)
                created_keys.append(vto_key)

                vto_stmt = select(CatalogImageTransformation).where(
                    CatalogImageTransformation.asset_id == asset.id,
                    CatalogImageTransformation.transformation_type
                    == TransformationType.VTO_INPUT.value,
                    CatalogImageTransformation.transformation_version == "v1",
                )
                existing_vto = (await self.session.scalars(vto_stmt)).first()
                if existing_vto is None:
                    vto_record = CatalogImageTransformation(
                        asset_id=asset.id,
                        transformation_type=TransformationType.VTO_INPUT.value,
                        transformation_version="v1",
                        processor_name=vto_deriv.processor_name,
                        processor_version=vto_deriv.processor_version,
                        storage_key=vto_key,
                        output_mime_type=vto_deriv.mime_type,
                        output_width=vto_deriv.width,
                        output_height=vto_deriv.height,
                        output_bytes=vto_deriv.byte_size,
                        output_sha256=vto_deriv.sha256,
                        status="ACTIVE",
                    )
                    self.session.add(vto_record)
                transform_names.append(TransformationType.VTO_INPUT.value)

            # Step 9: Link with CanonicalGarment if provided
            if request.canonical_garment_id and primary_display_key and primary_display_hash:
                garment_img_stmt = select(GarmentImage).where(
                    GarmentImage.garment_id == request.canonical_garment_id,
                    GarmentImage.content_hash == primary_display_hash,
                )
                existing_g_img = (await self.session.scalars(garment_img_stmt)).first()
                if existing_g_img is None:
                    g_img = GarmentImage(
                        garment_id=request.canonical_garment_id,
                        storage_key=primary_display_key,
                        content_hash=primary_display_hash,
                        perceptual_hash=inspected.perceptual_hash,
                        image_type="primary",
                        asset_id=asset.id,
                    )
                    self.session.add(g_img)

            await self.session.flush()

            result.success = True
            result.asset_id = asset.id
            result.status = asset.status
            result.original_storage_key = asset.original_storage_key
            result.transformations = transform_names
            return result

        except Exception as exc:
            # Step 10: Compensation cleanup if DB flush fails after uploads
            for key in created_keys:
                try:
                    await self.storage.delete(key)
                except Exception:
                    pass
            result.error_code = "db_commit_failed"
            result.error_message = f"Database operation failed; storage cleanup executed: {exc}"
            return result
