from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import (
    CatalogAuthorizationEvidence,
    CatalogPermissionStatus,
    CatalogSourcePermission,
    CatalogSourceStatus,
    EvidenceVerificationStatus,
    MerchantVerificationStatus,
)
from fashx.catalog.errors import SourceLifecycleError


class SourceLifecycleValidator:
    ALLOWED_TRANSITIONS: dict[str, list[str]] = {
        CatalogSourceStatus.PENDING_REVIEW.value: [
            CatalogSourceStatus.APPROVED.value,
            CatalogSourceStatus.REJECTED.value,
        ],
        CatalogSourceStatus.APPROVED.value: [
            CatalogSourceStatus.ACTIVE.value,
            CatalogSourceStatus.SUSPENDED.value,
            CatalogSourceStatus.REVOKED.value,
        ],
        CatalogSourceStatus.ACTIVE.value: [
            CatalogSourceStatus.SUSPENDED.value,
            CatalogSourceStatus.EXPIRED.value,
            CatalogSourceStatus.REVOKED.value,
        ],
        CatalogSourceStatus.SUSPENDED.value: [
            CatalogSourceStatus.ACTIVE.value,
            CatalogSourceStatus.REVOKED.value,
            CatalogSourceStatus.EXPIRED.value,
        ],
        CatalogSourceStatus.EXPIRED.value: [
            CatalogSourceStatus.PENDING_REVIEW.value,
            CatalogSourceStatus.APPROVED.value,
            CatalogSourceStatus.REVOKED.value,
        ],
        CatalogSourceStatus.REJECTED.value: [
            CatalogSourceStatus.PENDING_REVIEW.value,
        ],
        CatalogSourceStatus.REVOKED.value: [],
    }

    @classmethod
    def validate_transition(
        cls,
        source: CatalogSource,
        target_status: CatalogSourceStatus,
        merchant: Merchant | None,
        evidence_list: Sequence[CatalogAuthorizationEvidence],
        permissions_list: Sequence[CatalogSourcePermission],
    ) -> None:
        current_status = source.source_status
        target_val = target_status.value

        valid_targets = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        if target_val not in valid_targets:
            raise SourceLifecycleError(
                f"Invalid status transition from {current_status} to {target_val}.",
                code="invalid_source_transition",
            )

        # Transition to APPROVED requires a VERIFIED merchant
        if target_status == CatalogSourceStatus.APPROVED:
            if (
                not merchant
                or merchant.verification_status != MerchantVerificationStatus.VERIFIED.value
            ):
                raise SourceLifecycleError(
                    "Cannot approve source: Associated merchant is not VERIFIED.",
                    code="merchant_not_verified",
                )

        # Transition to ACTIVE requires:
        # 1. Merchant is VERIFIED
        # 2. At least one verified evidence record
        # 3. At least one active granted permission
        if target_status == CatalogSourceStatus.ACTIVE:
            if (
                not merchant
                or merchant.verification_status != MerchantVerificationStatus.VERIFIED.value
            ):
                raise SourceLifecycleError(
                    "Cannot activate source: Associated merchant is not VERIFIED.",
                    code="merchant_not_verified",
                )

            verified_evidence = [
                e
                for e in evidence_list
                if e.verification_status == EvidenceVerificationStatus.VERIFIED.value
            ]
            if not verified_evidence:
                raise SourceLifecycleError(
                    "Cannot activate source: Source has no verified authorization evidence.",
                    code="no_verified_evidence",
                )

            now = datetime.now(UTC)
            active_permissions = [
                p
                for p in permissions_list
                if p.permission_status == CatalogPermissionStatus.GRANTED.value
                and p.revoked_at is None
                and (p.expires_at is None or p.expires_at >= now)
            ]
            if not active_permissions:
                raise SourceLifecycleError(
                    "Cannot activate source: Source has no granted active permissions.",
                    code="no_active_permissions",
                )
