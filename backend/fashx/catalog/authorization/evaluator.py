from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import (
    CatalogAuthorizationEvidence,
    CatalogPermissionStatus,
    CatalogSourcePermission,
    CatalogSourceStatus,
    CatalogTakedownRequest,
    EvidenceVerificationStatus,
    MerchantVerificationStatus,
    TakedownStatus,
)
from fashx.catalog.authorization.schemas import AuthorizationContext


class EvaluationResult:
    def __init__(
        self,
        decision: str,  # ALLOW | DENY
        reason_code: str,
        permission_id: UUID | None = None,
    ) -> None:
        self.decision = decision
        self.reason_code = reason_code
        self.permission_id = permission_id

    @property
    def is_allowed(self) -> bool:
        return self.decision == "ALLOW"


class CatalogAuthorizationEvaluator:
    ACTIVE_TAKEDOWN_STATUSES = {
        TakedownStatus.RECEIVED.value,
        TakedownStatus.TRIAGED.value,
        TakedownStatus.SUSPENDED.value,
        TakedownStatus.PROCESSING.value,
        TakedownStatus.VERIFICATION.value,
    }

    @classmethod
    def evaluate(
        cls,
        context: AuthorizationContext,
        source: CatalogSource | None,
        merchant: Merchant | None,
        evidence_list: Sequence[CatalogAuthorizationEvidence],
        permissions_list: Sequence[CatalogSourcePermission],
        active_takedowns: Sequence[CatalogTakedownRequest],
        now: datetime | None = None,
    ) -> EvaluationResult:
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        # 1. Source existence check
        if not source:
            return EvaluationResult("DENY", "DENY_SOURCE_NOT_FOUND")

        # 2. Merchant verification check
        if (
            not merchant
            or merchant.verification_status != MerchantVerificationStatus.VERIFIED.value
        ):
            return EvaluationResult("DENY", "DENY_MERCHANT_NOT_VERIFIED")

        # 3. Source active check
        if source.source_status == CatalogSourceStatus.SUSPENDED.value:
            return EvaluationResult("DENY", "DENY_SOURCE_SUSPENDED")
        if source.source_status == CatalogSourceStatus.EXPIRED.value:
            return EvaluationResult("DENY", "DENY_SOURCE_EXPIRED")
        if source.source_status != CatalogSourceStatus.ACTIVE.value:
            return EvaluationResult("DENY", "DENY_SOURCE_NOT_ACTIVE")

        # 4. Active takedown check
        has_active_takedown = any(
            t.status in cls.ACTIVE_TAKEDOWN_STATUSES for t in active_takedowns
        )
        if has_active_takedown:
            return EvaluationResult("DENY", "DENY_SOURCE_TAKEDOWN_ACTIVE")

        # 5. Verified evidence check
        verified_evidence = [
            e
            for e in evidence_list
            if e.verification_status == EvidenceVerificationStatus.VERIFIED.value
        ]
        if not verified_evidence:
            return EvaluationResult("DENY", "DENY_NO_VERIFIED_EVIDENCE")

        # 6. Permission existence check (Strict Non-Inference Invariant)
        # Note: IMAGE_AI_PROCESS and VTO_PROCESS must NEVER be inferred from display/store.
        matching_permissions = [
            p for p in permissions_list if p.permission_code == context.operation
        ]
        if not matching_permissions:
            return EvaluationResult("DENY", "DENY_PERMISSION_NOT_FOUND")

        # 7. Permission status & revocation check
        has_revoked = any(
            p.permission_status == CatalogPermissionStatus.REVOKED.value or p.revoked_at is not None
            for p in matching_permissions
        )
        granted_permissions = [
            p
            for p in matching_permissions
            if p.permission_status == CatalogPermissionStatus.GRANTED.value and p.revoked_at is None
        ]
        if not granted_permissions:
            if has_revoked:
                return EvaluationResult("DENY", "DENY_PERMISSION_REVOKED")
            return EvaluationResult("DENY", "DENY_PERMISSION_NOT_GRANTED")

        unrevoked_permissions = granted_permissions

        # 9. Timing check: effective_at & expires_at
        timed_permissions = []
        is_future = False
        is_expired = False
        for p in unrevoked_permissions:
            eff = p.effective_at
            if eff.tzinfo is None:
                eff = eff.replace(tzinfo=UTC)
            if now < eff:
                is_future = True
                continue
            if p.expires_at is not None:
                exp = p.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=UTC)
                if now > exp:
                    is_expired = True
                    continue
            timed_permissions.append(p)

        if not timed_permissions:
            if is_future:
                return EvaluationResult("DENY", "DENY_PERMISSION_NOT_YET_EFFECTIVE")
            if is_expired:
                return EvaluationResult("DENY", "DENY_PERMISSION_EXPIRED")
            return EvaluationResult("DENY", "DENY_PERMISSION_TIMING_INVALID")

        # 10. Scope Categories check
        category_matched = []
        for p in timed_permissions:
            if not p.scope_categories or "*" in p.scope_categories or not context.category:
                category_matched.append(p)
            elif context.category in p.scope_categories:
                category_matched.append(p)

        if not category_matched:
            return EvaluationResult("DENY", "DENY_CATEGORY_OUT_OF_SCOPE")

        # 11. Scope Markets check
        market_matched = []
        for p in category_matched:
            if not p.scope_markets or "*" in p.scope_markets or not context.market:
                market_matched.append(p)
            elif context.market in p.scope_markets:
                market_matched.append(p)

        if not market_matched:
            return EvaluationResult("DENY", "DENY_MARKET_OUT_OF_SCOPE")

        # 12. Processor Restrictions check
        processor_matched = []
        for p in market_matched:
            if (
                not p.processor_restrictions
                or "*" in p.processor_restrictions
                or not context.processor_id
            ):
                processor_matched.append(p)
            elif context.processor_id in p.processor_restrictions:
                processor_matched.append(p)

        if not processor_matched:
            return EvaluationResult("DENY", "DENY_PROCESSOR_NOT_PERMITTED")

        selected_permission = processor_matched[0]
        return EvaluationResult(
            decision="ALLOW",
            reason_code="PERMITTED_BY_POLICY",
            permission_id=selected_permission.id,
        )
