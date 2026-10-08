from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.commerce.ports.affiliate import AffiliateProvider
from api.app.commerce.repository import CommerceRepository
from api.app.core.errors import ConflictError, NotFoundError
from api.app.core.idempotency import request_fingerprint
from api.app.repositories.idempotency import IdempotencyRepository
from api.app.core.transactions import transaction
from schemas.commerce.buy_click import BuyClickCreate, BuyClickResponse
from schemas.events.commerce import BuyClicked


class CommerceService:
    def __init__(
        self,
        commerce: CommerceRepository,
        catalog: CatalogRepository,
        affiliate: AffiliateProvider,
    ) -> None:
        self.commerce = commerce
        self.catalog = catalog
        self.affiliate = affiliate

    async def create_buy_click(
        self,
        *,
        user_id: UUID,
        request: BuyClickCreate,
        trace_id: UUID | None,
        idempotency_key: str | None = None,
    ) -> BuyClickResponse:
        async with transaction(self.commerce.session):
            if idempotency_key:
                idem_repo = IdempotencyRepository(self.commerce.session)
                existing = await idem_repo.get(user_id=user_id, key=idempotency_key)
                fingerprint = request_fingerprint(request.garment_id, request.offer_id)
                if existing is not None:
                    if existing.request_hash != fingerprint:
                        raise ConflictError("Idempotency-Key was already used with a different request")
                    if existing.state == "completed" and existing.response_body is not None and existing.status_code is not None:
                        return BuyClickResponse.model_validate(existing.response_body)
                    raise ConflictError("The same buy request is already being processed")
                await idem_repo.create_claim(user_id=user_id, key=idempotency_key, request_hash=fingerprint)

            offer = await self.catalog.get_offer(request.garment_id, request.offer_id)
            if offer is None:
                raise NotFoundError("Merchant offer not found")
            if not offer.in_stock:
                raise ConflictError("Selected merchant offer is unavailable")

            # Never accept a client-provided destination. The URL is read from the trusted catalog offer.
            tracking_id = str(uuid4())
            redirect = self.affiliate.build_redirect(
                merchant_url=offer.url,
                merchant_id=offer.merchant_id,
                offer_id=offer.id,
                tracking_id=tracking_id,
            )
            click = await self.commerce.create_buy_click(
                user_id=user_id,
                garment_id=request.garment_id,
                offer_id=offer.id,
                affiliate_network=redirect.affiliate_network,
                tracking_id=redirect.tracking_id,
            )
            event = BuyClicked.create(
                user_id=user_id,
                garment_id=request.garment_id,
                offer_id=offer.id,
                tracking_id=redirect.tracking_id,
                affiliate_network=redirect.affiliate_network,
                trace_id=trace_id,
                occurred_at=datetime.now(timezone.utc),
                event_id=uuid4(),
            )
            await self.commerce.create_event(
                event_id=event.event_id,
                event_type=event.event_type,
                schema_version=event.schema_version,
                user_id=event.user_id,
                object_type=event.object_type,
                object_id=event.object_id,
                trace_id=event.trace_id,
                occurred_at=event.occurred_at,
                payload=event.payload,
            )

            response = BuyClickResponse(
                buy_click_id=click.id,
                garment_id=request.garment_id,
                offer_id=offer.id,
                redirect_url=redirect.redirect_url,
                affiliate_network=redirect.affiliate_network,
                tracking_id=redirect.tracking_id,
            )
            if idempotency_key:
                idem_repo = IdempotencyRepository(self.commerce.session)
                record = await idem_repo.get(user_id=user_id, key=idempotency_key)
                if record is not None:
                    await idem_repo.complete(record, status_code=200, response_body=response.model_dump(mode="json"))
            return response


class OfferSelectionService:
    """Compatibility service for catalog offer validation."""

    def __init__(self, catalog) -> None:
        self.catalog = catalog

    async def validate_selection(self, garment_id: UUID, offer_id: UUID):
        offer = await self.catalog.get_offer(garment_id, offer_id)
        if offer is None:
            raise NotFoundError("Merchant offer not found")
        if not offer.in_stock:
            raise NotFoundError("Selected merchant offer is unavailable")
        return offer
