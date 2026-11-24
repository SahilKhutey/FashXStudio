"""VTO Input Validation orchestration and persistence service (Phase 07.3)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from .combined_validator import CombinedVTOInputValidator
from .contracts import (
    CombinedValidationResult,
    ImageValidationResult,
    ValidationRequest,
    ValidationStatus,
)
from .garment_validator import GarmentImageValidator
from .shopper_validator import ShopperImageValidator

log = logging.getLogger(__name__)


class VTOInputValidationService:
    """Orchestrates input image validation and persists durable audit records."""

    def __init__(
        self,
        validator: CombinedVTOInputValidator,
        tryon_uow: Any | None = None,
    ) -> None:
        self.validator = validator
        self.tryon_uow = tryon_uow

    @classmethod
    def create_default(
        cls,
        *,
        profile_uow: Any,
        catalog_uow: Any,
        storage: Any,
        tryon_uow: Any | None = None,
        authorization_service: Any | None = None,
    ) -> VTOInputValidationService:
        """Factory creating default validators using existing Unit of Work ports."""
        shopper_validator = ShopperImageValidator(
            consent_repository=profile_uow.consents if hasattr(profile_uow, "consents") else profile_uow,
            asset_repository=profile_uow.photos if hasattr(profile_uow, "photos") else profile_uow,
            storage=storage,
        )
        garment_validator = GarmentImageValidator(
            catalog_repository=catalog_uow.garments if hasattr(catalog_uow, "garments") else catalog_uow,
            authorization_service=authorization_service,
            storage=storage,
        )
        combined = CombinedVTOInputValidator(
            shopper_validator=shopper_validator,
            garment_validator=garment_validator,
        )
        return cls(validator=combined, tryon_uow=tryon_uow)

    async def validate_and_record(
        self,
        *,
        job_id: UUID,
        request: ValidationRequest,
    ) -> CombinedValidationResult:
        """Validate both inputs and persist durable audit evidence to database."""
        result = await self.validator.validate(request)

        # Persist audit evidence if unit of work is available
        if self.tryon_uow and hasattr(self.tryon_uow, "validations"):
            try:
                await self._persist_audit_records(job_id, result)
            except Exception as exc:
                log.warning("Failed persisting VTO validation audit records for job %s: %s", job_id, exc)

        return result

    async def _persist_audit_records(
        self,
        job_id: UUID,
        result: CombinedValidationResult,
    ) -> None:
        # 1. Record Shopper validation
        await self._record_single_validation(job_id, result.shopper)
        # 2. Record Garment validation
        await self._record_single_validation(job_id, result.garment)

        # 3. Record authorization snapshots if repo available
        if hasattr(self.tryon_uow, "auth_snapshots"):
            # Shopper consent snapshot
            consent_status = (
                "ALLOWED"
                if result.shopper.status in (ValidationStatus.PASSED, ValidationStatus.PASSED_WITH_WARNINGS)
                else "DENIED"
            )
            await self.tryon_uow.auth_snapshots.record_snapshot(
                tryon_job_id=job_id,
                authorization_type="CONSENT",
                subject_id=UUID(result.shopper.asset_id) if len(result.shopper.asset_id) == 36 else job_id,
                permission_scope="THIRD_PARTY_VTO_PROCESSING",
                policy_version=result.shopper.policy_version,
                result=consent_status,
            )

            # Garment permission snapshot
            garment_status = (
                "ALLOWED"
                if result.garment.status in (ValidationStatus.PASSED, ValidationStatus.PASSED_WITH_WARNINGS)
                else "DENIED"
            )
            await self.tryon_uow.auth_snapshots.record_snapshot(
                tryon_job_id=job_id,
                authorization_type="MERCHANT_PERMISSION",
                subject_id=UUID(result.garment.asset_id) if len(result.garment.asset_id) == 36 else job_id,
                permission_scope="VTO_PROCESS,IMAGE_AI_PROCESS",
                policy_version=result.garment.policy_version,
                result=garment_status,
            )

    async def _record_single_validation(
        self,
        job_id: UUID,
        item: ImageValidationResult,
    ) -> None:
        tech_dict = item.technical_metadata.model_dump() if item.technical_metadata else {}
        vis_dict = item.visual_metadata.model_dump() if item.visual_metadata else {}
        issues_list = [i.model_dump() for i in item.issues]

        asset_uuid = UUID(item.asset_id) if len(item.asset_id) == 36 else job_id

        await self.tryon_uow.validations.record_validation(
            tryon_job_id=job_id,
            role=item.role.value,
            asset_id=asset_uuid,
            asset_version=item.asset_version,
            policy_version=item.policy_version,
            status=item.status.value,
            original_sha256=item.technical_metadata.original_sha256 if item.technical_metadata else None,
            normalized_sha256=item.technical_metadata.normalized_sha256 if item.technical_metadata else None,
            technical_metadata=tech_dict,
            visual_metadata=vis_dict,
            issues=issues_list,
            validated_at=item.validated_at,
        )
