"""Combined two-image validation orchestrator for Phase 07.3."""

from __future__ import annotations

import logging
from typing import Any

from .contracts import (
    CombinedValidationResult,
    ValidationRequest,
    ValidationStatus,
)
from .garment_validator import GarmentImageValidator
from .shopper_validator import ShopperImageValidator

log = logging.getLogger(__name__)


class CombinedVTOInputValidator:
    """Coordinates validation across shopper reference photo and merchant garment image."""

    def __init__(
        self,
        shopper_validator: ShopperImageValidator,
        garment_validator: GarmentImageValidator,
        validation_repo: Any | None = None,
    ) -> None:
        self.shopper_validator = shopper_validator
        self.garment_validator = garment_validator
        self.validation_repo = validation_repo

    async def validate(self, request: ValidationRequest) -> CombinedValidationResult:
        """Execute validation across both images and synthesize combined verdict."""
        shopper_res = await self.shopper_validator.validate(
            user_id=request.user_id,
            asset_id=request.shopper_asset_id,
            garment_category=request.garment_category,
        )

        garment_res = await self.garment_validator.validate(
            product_id=request.product_id,
            image_asset_id=request.garment_image_asset_id,
            image_version=request.garment_image_version,
            garment_category=request.garment_category,
        )

        # Derive overall verdict (fail-closed order)
        if (
            shopper_res.status == ValidationStatus.ERROR
            or garment_res.status == ValidationStatus.ERROR
        ):
            status = ValidationStatus.ERROR
        elif (
            shopper_res.status == ValidationStatus.REJECTED
            or garment_res.status == ValidationStatus.REJECTED
        ):
            status = ValidationStatus.REJECTED
        elif (
            shopper_res.status == ValidationStatus.EXPIRED
            or garment_res.status == ValidationStatus.EXPIRED
        ):
            status = ValidationStatus.EXPIRED
        elif (
            shopper_res.status == ValidationStatus.NEEDS_REVIEW
            or garment_res.status == ValidationStatus.NEEDS_REVIEW
        ):
            status = ValidationStatus.NEEDS_REVIEW
        elif (
            shopper_res.status == ValidationStatus.PASSED_WITH_WARNINGS
            or garment_res.status == ValidationStatus.PASSED_WITH_WARNINGS
        ):
            status = ValidationStatus.PASSED_WITH_WARNINGS
        else:
            status = ValidationStatus.PASSED

        result = CombinedValidationResult(
            status=status,
            shopper=shopper_res,
            garment=garment_res,
        )

        log.info(
            "VTO Input Validation completed: user=%s, product=%s, status=%s, can_submit=%s",
            request.user_id,
            request.product_id,
            status.value,
            result.can_submit,
        )

        return result
