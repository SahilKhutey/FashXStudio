"""Shopper image authorization, ownership, technical, and visual validator."""

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
    BODY_REGION_NOT_VISIBLE,
    BODY_REGION_OCCLUDED,
    IMAGE_CORRUPTED,
    IMAGE_NOT_ACTIVE,
    IMAGE_NOT_OWNED_OR_NOT_FOUND,
    MULTIPLE_PEOPLE_DETECTED,
    PERSON_NOT_DETECTED,
    POSE_UNSUPPORTED,
    UNSUPPORTED_GARMENT_CATEGORY,
    VTO_CONSENT_REQUIRED,
    get_user_remediation_message,
)
from .image_inspector import ImageInspectionError, ImageInspector
from .visual_assessment import (
    HeuristicVisualAssessmentProvider,
    VisualAssessmentProvider,
    VisualAssessmentRequest,
)


class ShopperImageValidator:
    """Validates shopper consent, ownership, raster integrity, and visual suitability."""

    def __init__(
        self,
        consent_repository: Any,
        asset_repository: Any,
        storage: Any,
        inspector: ImageInspector | None = None,
        visual_provider: VisualAssessmentProvider | None = None,
        config: ImageValidationConfig | None = None,
    ) -> None:
        self.consent_repository = consent_repository
        self.asset_repository = asset_repository
        self.storage = storage
        self.config = config or ImageValidationConfig()
        self.inspector = inspector or ImageInspector(self.config)
        self.visual_provider = visual_provider or HeuristicVisualAssessmentProvider()

    async def validate(
        self,
        *,
        user_id: UUID,
        asset_id: UUID,
        garment_category: str = "tops",
    ) -> ImageValidationResult:
        asset_id_str = str(asset_id)
        issues: list[ValidationIssue] = []

        # 1. Authoritative VTO Consent Check (Rule I06 & DPDP)
        has_consent = False
        try:
            # First probe dedicated third-party VTO consent
            if hasattr(self.consent_repository, "has_active_consent"):
                res = self.consent_repository.has_active_consent(
                    user_id=user_id, purpose="THIRD_PARTY_VTO_PROCESSING"
                )
                has_consent = await res if inspect.isawaitable(res) else bool(res)
            elif hasattr(self.consent_repository, "has_consent"):
                res = self.consent_repository.has_consent(user_id, "THIRD_PARTY_VTO_PROCESSING")
                has_consent = await res if inspect.isawaitable(res) else bool(res)

            # Fallback to general body photo consent if not yet migrated to granular tag
            if not has_consent and hasattr(self.consent_repository, "has_consent"):
                res = self.consent_repository.has_consent(user_id, "body_photo")
                has_consent = await res if inspect.isawaitable(res) else bool(res)
        except Exception:
            has_consent = False

        if not has_consent:
            issues.append(
                ValidationIssue(
                    code=VTO_CONSENT_REQUIRED,
                    severity=Severity.ERROR,
                    message="Active virtual try-on processing consent is missing or withdrawn",
                    user_message=get_user_remediation_message(VTO_CONSENT_REQUIRED),
                )
            )
            return ImageValidationResult(
                role=ImageRole.SHOPPER,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version="unknown",
                policy_version=self.config.policy_version,
                issues=issues,
            )

        # 2. Asset Ownership and Status (Anti-enumeration: reject cross-user access)
        photo = None
        try:
            if hasattr(self.asset_repository, "get_by_id"):
                res = self.asset_repository.get_by_id(asset_id)
                photo = await res if inspect.isawaitable(res) else res
            elif hasattr(self.asset_repository, "get_owned_photo"):
                res = self.asset_repository.get_owned_photo(asset_id=asset_id, user_id=user_id)
                photo = await res if inspect.isawaitable(res) else res
        except Exception:
            photo = None

        if photo is None or getattr(photo, "user_id", None) != user_id:
            issues.append(
                ValidationIssue(
                    code=IMAGE_NOT_OWNED_OR_NOT_FOUND,
                    severity=Severity.ERROR,
                    message="Asset not found or not owned by authenticated user",
                    user_message=get_user_remediation_message(IMAGE_NOT_OWNED_OR_NOT_FOUND),
                )
            )
            return ImageValidationResult(
                role=ImageRole.SHOPPER,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version="unknown",
                policy_version=self.config.policy_version,
                issues=issues,
            )

        asset_status = str(getattr(photo, "status", "pending")).lower()
        if asset_status not in ("accepted", "available"):
            issues.append(
                ValidationIssue(
                    code=IMAGE_NOT_ACTIVE,
                    severity=Severity.ERROR,
                    message=f"Shopper asset is in inactive status '{asset_status}'",
                    user_message=get_user_remediation_message(IMAGE_NOT_ACTIVE),
                )
            )
            return ImageValidationResult(
                role=ImageRole.SHOPPER,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=str(getattr(photo, "version", 1)),
                policy_version=self.config.policy_version,
                issues=issues,
            )

        storage_key = getattr(photo, "storage_key", None)
        if not storage_key:
            issues.append(
                ValidationIssue(
                    code=IMAGE_CORRUPTED,
                    severity=Severity.ERROR,
                    message="Missing storage key reference for photo",
                    user_message=get_user_remediation_message(IMAGE_CORRUPTED),
                )
            )
            return ImageValidationResult(
                role=ImageRole.SHOPPER,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=str(getattr(photo, "version", 1)),
                policy_version=self.config.policy_version,
                issues=issues,
            )

        # 3. Retrieve and inspect image bytes
        raw_bytes: bytes | None = None
        try:
            get_res = self.storage.get(storage_key)
            raw_bytes = await get_res if inspect.isawaitable(get_res) else get_res
        except Exception:
            raw_bytes = None

        if not raw_bytes:
            issues.append(
                ValidationIssue(
                    code=IMAGE_CORRUPTED,
                    severity=Severity.ERROR,
                    message="Failed to read image payload from private storage",
                    user_message=get_user_remediation_message(IMAGE_CORRUPTED),
                )
            )
            return ImageValidationResult(
                role=ImageRole.SHOPPER,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=str(getattr(photo, "version", 1)),
                policy_version=self.config.policy_version,
                issues=issues,
            )

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
                role=ImageRole.SHOPPER,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=str(getattr(photo, "version", 1)),
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

        # 4. Category Policy & Visual Assessment
        policy = get_category_policy(garment_category)
        if policy.status == CategorySupportStatus.UNSUPPORTED:
            issues.append(
                ValidationIssue(
                    code=UNSUPPORTED_GARMENT_CATEGORY,
                    severity=Severity.ERROR,
                    message=f"Category '{garment_category}' is unsupported: {policy.description}",
                    user_message=get_user_remediation_message(UNSUPPORTED_GARMENT_CATEGORY),
                )
            )
            return ImageValidationResult(
                role=ImageRole.SHOPPER,
                status=ValidationStatus.REJECTED,
                asset_id=asset_id_str,
                asset_version=str(getattr(photo, "version", 1)),
                policy_version=self.config.policy_version,
                technical_metadata=tech_meta,
                issues=issues,
            )

        vis_req = VisualAssessmentRequest(
            image_role="SHOPPER",
            garment_category=garment_category,
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
                role=ImageRole.SHOPPER,
                status=ValidationStatus.ERROR,
                asset_id=asset_id_str,
                asset_version=str(getattr(photo, "version", 1)),
                policy_version=self.config.policy_version,
                technical_metadata=tech_meta,
                issues=issues,
            )

        vis_meta = VisualMetadata(
            person_detected=vis_resp.person_detected,
            person_count=vis_resp.person_count,
            visible_regions=vis_resp.visible_regions,
            pose_label=vis_resp.pose_label,
            pose_confidence=vis_resp.pose_confidence,
            occlusion_detected=vis_resp.occlusion_detected,
            confidence=vis_resp.confidence,
            model_name=vis_resp.model_name,
            model_version=vis_resp.model_version,
        )

        # Evaluate visual findings
        has_blocking_error = False

        if vis_resp.person_detected is False:
            has_blocking_error = True
            issues.append(
                ValidationIssue(
                    code=PERSON_NOT_DETECTED,
                    severity=Severity.ERROR,
                    message="No person detected in shopper reference photo",
                    user_message=get_user_remediation_message(PERSON_NOT_DETECTED),
                )
            )

        if (
            self.config.reject_multiple_people
            and vis_resp.person_count is not None
            and vis_resp.person_count > 1
        ):
            has_blocking_error = True
            issues.append(
                ValidationIssue(
                    code=MULTIPLE_PEOPLE_DETECTED,
                    severity=Severity.ERROR,
                    message=f"Multiple people detected ({vis_resp.person_count}) in photo",
                    user_message=get_user_remediation_message(MULTIPLE_PEOPLE_DETECTED),
                )
            )

        # Check required body regions for category
        missing_regions = policy.required_regions - set(vis_resp.visible_regions)
        if missing_regions:
            has_blocking_error = True
            issues.append(
                ValidationIssue(
                    code=BODY_REGION_NOT_VISIBLE,
                    severity=Severity.ERROR,
                    message=f"Required regions for {garment_category} missing: {sorted(missing_regions)}",
                    user_message=get_user_remediation_message(BODY_REGION_NOT_VISIBLE),
                    metadata={"missing_regions": sorted(missing_regions)},
                )
            )

        # Pose check
        if vis_resp.pose_label == "LYING_DOWN":
            has_blocking_error = True
            issues.append(
                ValidationIssue(
                    code=POSE_UNSUPPORTED,
                    severity=Severity.ERROR,
                    message="Unsupported pose: lying down",
                    user_message=get_user_remediation_message(POSE_UNSUPPORTED),
                )
            )

        # Occlusion check
        if vis_resp.occlusion_detected:
            if vis_resp.occlusion_severity == "SEVERE":
                has_blocking_error = True
                issues.append(
                    ValidationIssue(
                        code=BODY_REGION_OCCLUDED,
                        severity=Severity.ERROR,
                        message="Severe occlusion detected over target garment area",
                        user_message=get_user_remediation_message(BODY_REGION_OCCLUDED),
                    )
                )
            else:
                issues.append(
                    ValidationIssue(
                        code=BODY_REGION_OCCLUDED,
                        severity=Severity.WARNING,
                        message="Minor occlusion detected near garment border",
                        user_message="Keep hands and items slightly farther from the clothing area.",
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
            role=ImageRole.SHOPPER,
            status=status,
            asset_id=asset_id_str,
            asset_version=str(getattr(photo, "version", 1)),
            policy_version=self.config.policy_version,
            technical_metadata=tech_meta,
            visual_metadata=vis_meta,
            issues=issues,
        )
