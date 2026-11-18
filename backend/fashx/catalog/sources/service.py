from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import (
    CatalogAuthorizationEvidence,
    CatalogSourcePermission,
    CatalogSourceStatus,
)
from fashx.catalog.errors import (
    MerchantNotFoundError,
    SourceLifecycleError,
    SourceNotFoundError,
)
from fashx.catalog.sources.lifecycle import SourceLifecycleValidator
from fashx.catalog.sources.repository import CatalogSourceRepository
from fashx.catalog.sources.schemas import (
    SourceCreate,
    SourceStatusUpdate,
    SourceUpdate,
)


class CatalogSourceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CatalogSourceRepository(session)

    async def register_source(self, payload: SourceCreate) -> CatalogSource:
        # Check merchant exists
        merchant_res = await self.session.execute(
            select(Merchant).where(Merchant.id == payload.merchant_id)
        )
        merchant = merchant_res.scalar_one_or_none()
        if not merchant:
            raise MerchantNotFoundError(payload.merchant_id)

        # Check slug uniqueness
        existing_slug = await self.repo.get_by_slug(payload.slug)
        if existing_slug:
            raise SourceLifecycleError(
                f"Catalog source with slug '{payload.slug}' already exists.",
                code="source_slug_conflict",
            )

        source = CatalogSource(
            merchant_id=payload.merchant_id,
            slug=payload.slug,
            name=payload.name,
            kind=payload.source_type.value.lower(),
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
            refresh_hours=payload.refresh_hours,
            max_rps=payload.max_rps,
            terms_url=payload.terms_url,
            takedown_contact=payload.takedown_contact,
            source_name=payload.source_name or payload.name,
            source_type=payload.source_type.value,
            source_owner=payload.source_owner,
            provider_name=payload.provider_name,
            source_description=payload.source_description,
            access_method=payload.access_method.value,
            credential_secret_ref=payload.credential_secret_ref,
            source_status=CatalogSourceStatus.PENDING_REVIEW.value,
            market_codes=payload.market_codes,
            category_codes=payload.category_codes,
            effective_at=payload.effective_at,
            expires_at=payload.expires_at,
            next_review_at=payload.next_review_at,
        )
        return await self.repo.create(source)

    async def get_source(self, source_id: UUID) -> CatalogSource:
        source = await self.repo.get_by_id(source_id)
        if not source:
            raise SourceNotFoundError(source_id)
        return source

    async def update_source(self, source_id: UUID, payload: SourceUpdate) -> CatalogSource:
        source = await self.get_source(source_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "source_type" in update_data and update_data["source_type"]:
            update_data["source_type"] = update_data["source_type"].value
        if "access_method" in update_data and update_data["access_method"]:
            update_data["access_method"] = update_data["access_method"].value

        for field, value in update_data.items():
            setattr(source, field, value)

        return await self.repo.update(source)

    async def update_source_status(self, source_id: UUID, req: SourceStatusUpdate) -> CatalogSource:
        source = await self.get_source(source_id)

        merchant: Merchant | None = None
        if source.merchant_id:
            m_res = await self.session.execute(
                select(Merchant).where(Merchant.id == source.merchant_id)
            )
            merchant = m_res.scalar_one_or_none()

        ev_res = await self.session.execute(
            select(CatalogAuthorizationEvidence).where(
                CatalogAuthorizationEvidence.source_id == source.id
            )
        )
        evidence_list = ev_res.scalars().all()

        perm_res = await self.session.execute(
            select(CatalogSourcePermission).where(CatalogSourcePermission.source_id == source.id)
        )
        permissions_list = perm_res.scalars().all()

        SourceLifecycleValidator.validate_transition(
            source=source,
            target_status=req.target_status,
            merchant=merchant,
            evidence_list=evidence_list,
            permissions_list=permissions_list,
        )

        source.source_status = req.target_status.value
        if req.target_status == CatalogSourceStatus.ACTIVE:
            source.status = "cleared"
            source.rights_display = True
        elif req.target_status in (
            CatalogSourceStatus.SUSPENDED,
            CatalogSourceStatus.REVOKED,
            CatalogSourceStatus.EXPIRED,
            CatalogSourceStatus.REJECTED,
        ):
            source.status = "suspended"
            source.rights_display = False
            source.rights_tryon = False

        return await self.repo.update(source)

    async def suspend_source(self, source_id: UUID, reason: str) -> CatalogSource:
        return await self.update_source_status(
            source_id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.SUSPENDED,
                reason=reason,
            ),
        )

    async def resume_source(self, source_id: UUID, reason: str) -> CatalogSource:
        return await self.update_source_status(
            source_id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.ACTIVE,
                reason=reason,
            ),
        )

    async def list_sources(
        self,
        merchant_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[CatalogSource]:
        return await self.repo.list_sources(
            merchant_id=merchant_id, status=status, limit=limit, offset=offset
        )
