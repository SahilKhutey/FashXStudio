"""Merchant authorization, product association, technical, and visual garment validator."""

from __future__ import annotations

import inspect
from typing import Any
from uuid import UUID

from .category_policy import CategorySupportStatus, get_category_policy
from .config import ImageValidationConfig
from .contracts import (
    ImageRole,
    ImageValidationResult,
    Severity,
    TechnicalMetadata,
    ValidationIssue,
    ValidationStatus,
    VisualMetadata,
)
from .error_codes import (
    GARMENT_BACKGROUND_UNSUITABLE,
    GARMENT_NOT_VISIBLE,
    GARMENT_PROCESSING_NOT_AUTHORIZED,
    IMAGE_CORRUPTED,
    IMAGE_PRODUCT_MISMATCH,
    PRODUCT_NOT_ACTIVE,
    UNSUPPORTED_GARMENT_CATEGORY,
    get_user_remediation_message,
)
from .image_inspector import ImageInspectionError, ImageInspector
from .visual_assessment import (
    HeuristicVisualAssessmentProvider,
    VisualAssessmentProvider,
    VisualAssessmentRequest,
)


class GarmentImageValidator:
    """Validates merchant permissions, product association, image integrity, and garment suitability."""

    REQUIRED_PERMISSIONS = (
        "IMAGE_AI_PROCESS",
        "VTO_PROCESS",
    )

    def __init__(
        self,
        catalog_repository: Any,
        authorization_service: Any,
        storage: Any,
        inspector: ImageInspector | None = None,
        visual_provider: VisualAssessmentProvider | None = None,
        config: ImageValidationConfig | None = None,
    ) -> None:
        self.catalog_repository = catalog_repository
        self.authorization_service = authorization_service
        self.storage = storage
        self.config = config or ImageValidationConfig()
        self.inspector = inspector or ImageInspector(self.config)
        self.visual_provider = visual_provider or HeuristicVisualAssessmentProvider()

    async def validate(
        self,
        *,
        product_id: UUID,
        image_asset_id: UUID | None = None,
        image_version: str = "v1",
        garment_category: str = "tops",
    ) -> ImageValidationResult:
        asset_id_str = str(image_asset_id or product_id)
        issues: list[ValidationIssue] = []

        # 1. Product Status and Association Check
        product = None
        try:
            if hasattr(self.catalog_repository, "get_by_id"):
                res = self.catalog_repository.get_by_id(product_id)
                product = await res if inspect.isawaitable(res) else res
            elif hasattr(self.catalog_repository, "get_product"):
                res = self.catalog_repository.get_product(product_id)
                product = await res if inspect.isawaitable(res) else res
            elif hasattr(self.catalog_repository, "get_canonical_garment"):
                res = self.catalog_repository.get_canonical_garment(product_id)
                product = await res if inspect.isawaitable(res) else res
        except Exception:
            product = None

        if product is None:
            issues.append(
                ValidationIssue(
                    code=PRODUCT_NOT_ACTIVE,
                    severity=Severity.ERROR,
                    message=f"Product '{product_id}' not found in catalog",
                    user_message=get_user_remediation_message(PRODUCT_NOT_ACTIVE),
                )
            )
            return ImageValidationResult(
                role=ImageRole.GARMENT,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=image_version,
                policy_version=self.config.policy_version,
                issues=issues,
            )

        prod_status = str(getattr(product, "status", "ACTIVE")).upper()
        if prod_status in ("DELISTED", "TAKEDOWN", "SUSPENDED", "DISCONTINUED"):
            issues.append(
                ValidationIssue(
                    code=PRODUCT_NOT_ACTIVE,
                    severity=Severity.ERROR,
                    message=f"Product '{product_id}' is in inactive status '{prod_status}'",
                    user_message=get_user_remediation_message(PRODUCT_NOT_ACTIVE),
                )
            )
            return ImageValidationResult(
                role=ImageRole.GARMENT,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=image_version,
                policy_version=self.config.policy_version,
                issues=issues,
            )

        # 2. Product-to-Image Association
        image_record = None
        if image_asset_id is not None and hasattr(self.catalog_repository, "get_product_image"):
            try:
                res = self.catalog_repository.get_product_image(
                    product_id=product_id, image_asset_id=image_asset_id
                )
                image_record = await res if inspect.isawaitable(res) else res
            except Exception:
                image_record = None

            if image_record is None:
                issues.append(
                    ValidationIssue(
                        code=IMAGE_PRODUCT_MISMATCH,
                        severity=Severity.ERROR,
                        message=f"Image '{image_asset_id}' is not associated with product '{product_id}'",
                        user_message=get_user_remediation_message(IMAGE_PRODUCT_MISMATCH),
                    )
                )
                return ImageValidationResult(
                    role=ImageRole.GARMENT,
                    status=ValidationStatus.REJECTED,
                    asset_id=asset_id_str,
                    asset_version=image_version,
                    policy_version=self.config.policy_version,
                    issues=issues,
                )

        # 3. Merchant Permission Verification (IMAGE_AI_PROCESS, VTO_PROCESS)
        source_id = getattr(product, "source_id", None)
        permissions_ok = True
        if self.authorization_service is not None:
            try:
                if hasattr(self.authorization_service, "has_permissions"):
                    res = self.authorization_service.has_permissions(
                        source_id=source_id,
                        required_permissions=self.REQUIRED_PERMISSIONS,
                    )
                    permissions_ok = await res if inspect.isawaitable(res) else bool(res)
                elif hasattr(self.authorization_service, "check_source_permission"):
                    for perm in self.REQUIRED_PERMISSIONS:
                        res = self.authorization_service.check_source_permission(
                            source_id=source_id,
                            permission_code=perm,
                        )
                        perm_val = await res if inspect.isawaitable(res) else bool(res)
                        if not perm_val:
                            permissions_ok = False
                            break
            except Exception:
                permissions_ok = False

        if not permissions_ok:
            issues.append(
                ValidationIssue(
                    code=GARMENT_PROCESSING_NOT_AUTHORIZED,
                    severity=Severity.ERROR,
                    message="Merchant permission missing for VTO_PROCESS or IMAGE_AI_PROCESS",
                    user_message=get_user_remediation_message(GARMENT_PROCESSING_NOT_AUTHORIZED),
                )
            )
            return ImageValidationResult(
                role=ImageRole.GARMENT,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=image_version,
                policy_version=self.config.policy_version,
                issues=issues,
            )

        # 4. Resolve Storage Key & Retrieve Image
        storage_key = (
            getattr(image_record, "storage_key", None)
            or getattr(image_record, "original_storage_key", None)
            or getattr(product, "image_storage_key", None)
            or getattr(product, "storage_key", None)
        )
        raw_bytes: bytes | None = None
        if storage_key and self.storage is not None:
            try:
                get_res = self.storage.get(storage_key)
                raw_bytes = await get_res if inspect.isawaitable(get_res) else get_res
            except Exception:
                raw_bytes = None

        # Fallback if image bytes are directly available on product
        if raw_bytes is None and hasattr(product, "image_bytes"):
            raw_bytes = product.image_bytes

        if not raw_bytes:
            issues.append(
                ValidationIssue(
                    code=IMAGE_CORRUPTED,
                    severity=Severity.ERROR,
                    message="Failed to retrieve garment image bytes from storage",
                    user_message=get_user_remediation_message(IMAGE_CORRUPTED),
                )
            )
            return ImageValidationResult(
                role=ImageRole.GARMENT,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=image_version,
                policy_version=self.config.policy_version,
                issues=issues,
            )

        # 5. Technical Image Inspection
        try:
            inspected = self.inspector.inspect(raw_bytes)
        except ImageInspectionError as ie:
            issues.append(
                ValidationIssue(
                    code=ie.code,
                    severity=Severity.ERROR,
                    message=ie.detail,
                    user_message=get_user_remediation_message(ie.code),
                )
            )
            return ImageValidationResult(
                role=ImageRole.GARMENT,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=image_version,
                policy_version=self.config.policy_version,
                issues=issues,
            )

        tech_meta = TechnicalMetadata(
            width=inspected.width,
            height=inspected.height,
            format=inspected.detected_format,
            size_bytes=inspected.original_size_bytes,
            original_sha256=inspected.original_sha256,
            normalized_sha256=inspected.normalized_sha256,
        )

        # 6. Supported Category Check
        category = garment_category or getattr(product, "category", "tops")
        policy = get_category_policy(category)
        if policy.status == CategorySupportStatus.UNSUPPORTED:
            issues.append(
                ValidationIssue(
                    code=UNSUPPORTED_GARMENT_CATEGORY,
                    severity=Severity.ERROR,
                    message=f"Category '{category}' is unsupported: {policy.description}",
                    user_message=get_user_remediation_message(UNSUPPORTED_GARMENT_CATEGORY),
                )
            )
            return ImageValidationResult(
                role=ImageRole.GARMENT,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=image_version,
                policy_version=self.config.policy_version,
                technical_metadata=tech_meta,
                issues=issues,
            )

        # 7. Garment Visual Assessment
        vis_req = VisualAssessmentRequest(
            image_role="GARMENT",
            garment_category=category,
            image_bytes=inspected.normalized_bytes,
        )
        try:
            vis_resp = await self.visual_provider.assess(vis_req)
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    code="IMAGE_VALIDATION_UNAVAILABLE",
                    severity=Severity.ERROR,
                    message=f"Visual assessment service failed: {exc}",
                    user_message=get_user_remediation_message("IMAGE_VALIDATION_UNAVAILABLE"),
                )
            )
            return ImageValidationResult(
                role=ImageRole.GARMENT,
                status=ValidationStatus.ERROR,
                asset_id=asset_id_str,
                asset_version=image_version,
                policy_version=self.config.policy_version,
                technical_metadata=tech_meta,
                issues=issues,
            )

        vis_meta = VisualMetadata(
            garment_visible=vis_resp.garment_visible,
            background_suitable=vis_resp.background_suitable,
            confidence=vis_resp.confidence,
            model_name=vis_resp.model_name,
            model_version=vis_resp.model_version,
        )

        has_blocking_error = False

        if vis_resp.garment_visible is False:
            has_blocking_error = True
            issues.append(
                ValidationIssue(
                    code=GARMENT_NOT_VISIBLE,
                    severity=Severity.ERROR,
                    message="Garment could not be distinguished in product image",
                    user_message=get_user_remediation_message(GARMENT_NOT_VISIBLE),
                )
            )

        if vis_resp.background_suitable is False:
            issues.append(
                ValidationIssue(
                    code=GARMENT_BACKGROUND_UNSUITABLE,
                    severity=Severity.WARNING,
                    message="Garment background has high clutter or poor contrast",
                    user_message=get_user_remediation_message(GARMENT_BACKGROUND_UNSUITABLE),
                )
            )

        if has_blocking_error:
            status = ValidationStatus.REJECTED
        elif vis_resp.confidence < self.config.visual_confidence_threshold:
            status = ValidationStatus.NEEDS_REVIEW
        elif any(issue.severity == Severity.WARNING for issue in issues):
            status = ValidationStatus.PASSED_WITH_WARNINGS
        else:
            status = ValidationStatus.PASSED

        return ImageValidationResult(
            role=ImageRole.GARMENT,
            status=status,
            asset_id=asset_id_str,
            asset_version=image_version,
            policy_version=self.config.policy_version,
            technical_metadata=tech_meta,
            visual_metadata=vis_meta,
            issues=issues,
        )
