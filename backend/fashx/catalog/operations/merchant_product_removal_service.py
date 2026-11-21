from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CanonicalGarment, MerchantOffer, MerchantProduct
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    AuditOutcome,
)
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    MerchantOfferDeactivateRequest,
    MerchantOfferDeactivateResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService


class MerchantProductRemovalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = SourceAuditService(session)

    async def deactivate_offer(
        self,
        offer_id: UUID,
        payload: MerchantOfferDeactivateRequest,
        merchant_id: UUID,
        actor_id: UUID | None = None,
        actor_role: str = AuditActorRole.MERCHANT_OPERATOR.value,
    ) -> MerchantOfferDeactivateResponse:
        offer = await self.session.get(MerchantOffer, offer_id)
        if not offer:
            raise CatalogAuthorizationError(
                f"Merchant offer '{offer_id}' not found.",
                code="offer_not_found",
            )

        if offer.merchant_id != merchant_id:
            raise CatalogAuthorizationError(
                f"Access denied: offer does not belong to merchant '{merchant_id}'.",
                code="tenant_isolation_violation",
            )

        now = datetime.now(UTC)

        # 1. Deactivate this merchant offer
        offer.status = "INACTIVE"
        offer.in_stock = False
        offer.updated_at = now

        # Also deactivate corresponding MerchantProduct if present
        if offer.merchant_product_id:
            m_prod = await self.session.get(MerchantProduct, offer.merchant_product_id)
            if m_prod:
                m_prod.status = "inactive"
                m_prod.availability = "OUT_OF_STOCK"
                m_prod.updated_at = now

        # 2. Check remaining active offers for the shared canonical garment
        other_active_offers_count = (
            await self.session.scalar(
                select(func.count())
                .select_from(MerchantOffer)
                .where(
                    MerchantOffer.garment_id == offer.garment_id,
                    MerchantOffer.id != offer.id,
                    MerchantOffer.status == "ACTIVE",
                    MerchantOffer.in_stock.is_(True),
                )
            )
            or 0
        )

        garment = await self.session.get(CanonicalGarment, offer.garment_id)
        canonical_garment_active = True
        if garment:
            if other_active_offers_count == 0:
                # No other merchant offers this garment active
                garment.active = False
                garment.in_stock = False
                canonical_garment_active = False
            else:
                # Garment stays active because other merchants still offer it!
                canonical_garment_active = True
            garment.updated_at = now

        # 3. Log audit event
        await self.audit_service.log_event(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=merchant_id,
            source_id=offer.source_id,
            entity_type="OFFER",
            entity_id=str(offer.id),
            action=AuditAction.OFFER_DEACTIVATED.value,
            reason_code=payload.reason or "OPERATOR_OFFER_DEACTIVATION",
            safe_change_summary={
                "garment_id": str(offer.garment_id),
                "other_active_offers_remaining": other_active_offers_count,
                "canonical_garment_retained": canonical_garment_active,
            },
            outcome=AuditOutcome.SUCCESS.value,
        )

        await self.session.commit()

        return MerchantOfferDeactivateResponse(
            offer_id=offer.id,
            merchant_id=merchant_id,
            garment_id=offer.garment_id,
            offer_status="INACTIVE",
            canonical_garment_active=canonical_garment_active,
            deactivated_at=now,
        )
