from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import MerchantProduct
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    AuditOutcome,
    MerchantProductOverride,
)
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    MerchantProductOverrideRequest,
    MerchantProductOverrideResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService

ALLOWED_OVERRIDE_FIELDS = {
    "title",
    "description",
    "price_minor",
    "availability",
    "is_active",
}

DISALLOWED_SOURCE_MANAGED_FIELDS = {
    "source_product_id",
    "source_url",
    "source_id",
    "item_group_id",
    "content_hash",
    "source_schema_version",
}


class MerchantProductUpdateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = SourceAuditService(session)

    async def apply_product_override(
        self,
        product_id: UUID,
        payload: MerchantProductOverrideRequest,
        merchant_id: UUID,
        actor_id: UUID | None = None,
        actor_role: str = AuditActorRole.MERCHANT_OPERATOR.value,
    ) -> MerchantProductOverrideResponse:
        product = await self.session.get(MerchantProduct, product_id)
        if not product:
            raise CatalogAuthorizationError(
                f"Merchant product '{product_id}' not found.",
                code="product_not_found",
            )

        # Enforce merchant tenant ownership
        if product.merchant_id != merchant_id:
            raise CatalogAuthorizationError(
                f"Access denied: product does not belong to merchant '{merchant_id}'.",
                code="tenant_isolation_violation",
            )

        # Enforce field ownership rules
        field_name = payload.field_name.lower().strip()
        if (
            field_name in DISALLOWED_SOURCE_MANAGED_FIELDS
            or field_name not in ALLOWED_OVERRIDE_FIELDS
        ):
            raise CatalogAuthorizationError(
                f"Field '{field_name}' is source-managed or not permitted for manual merchant override. "
                f"Allowed fields: {sorted(ALLOWED_OVERRIDE_FIELDS)}",
                code="field_override_disallowed",
            )

        now = datetime.now(UTC)

        # Check existing override
        existing = await self.session.scalar(
            select(MerchantProductOverride).where(
                MerchantProductOverride.merchant_id == merchant_id,
                MerchantProductOverride.merchant_product_id == product_id,
                MerchantProductOverride.field_name == field_name,
            )
        )

        previous_val = None
        if existing:
            previous_val = existing.override_value
            existing.previous_value = previous_val
            existing.override_value = payload.override_value
            existing.reason = payload.reason
            existing.updated_at = now
            override_record = existing
        else:
            # Get current value from product as previous
            current_raw = getattr(product, field_name, None)
            previous_val = {"value": current_raw} if current_raw is not None else None
            override_record = MerchantProductOverride(
                merchant_id=merchant_id,
                merchant_product_id=product_id,
                field_name=field_name,
                override_value=payload.override_value,
                previous_value=previous_val,
                reason=payload.reason,
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            self.session.add(override_record)

        # Apply override directly to product model for immediate effect
        new_val = payload.override_value.get("value")
        if field_name == "title" and isinstance(new_val, str):
            product.title = new_val
        elif field_name == "description" and isinstance(new_val, str):
            product.description = new_val
        elif field_name == "availability" and isinstance(new_val, str):
            product.availability = new_val
        elif field_name == "price_minor" and isinstance(new_val, (int, float)):
            product.price_minor = int(new_val)

        product.updated_at = now

        # Immutable audit trail
        await self.audit_service.log_event(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=merchant_id,
            source_id=product.source_id,
            entity_type="PRODUCT_OVERRIDE",
            entity_id=str(product_id),
            action=AuditAction.PRODUCT_OVERRIDE_SET.value,
            reason_code=payload.reason or "OPERATOR_OVERRIDE",
            safe_change_summary={
                "field_name": field_name,
                "previous_value": previous_val,
                "new_value": payload.override_value,
            },
            outcome=AuditOutcome.SUCCESS.value,
        )

        await self.session.commit()
        await self.session.refresh(override_record)

        return MerchantProductOverrideResponse(
            id=override_record.id,
            merchant_id=override_record.merchant_id,
            merchant_product_id=override_record.merchant_product_id,
            field_name=override_record.field_name,
            override_value=override_record.override_value,
            previous_value=override_record.previous_value,
            reason=override_record.reason,
            updated_at=override_record.updated_at,
        )
