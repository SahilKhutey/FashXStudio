from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import CatalogSourceStatus
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    AuditOutcome,
    CatalogSourceSchedule,
    OperationalStatus,
    SyncMode,
)
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    SourceConnectionRequest,
    SourceConnectionResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService


def mask_credential_reference(secret_ref: str | None) -> str | None:
    if not secret_ref:
        return None
    # If it is a URI, mask the last path component or query
    if "://" in secret_ref:
        prefix, sep, suffix = secret_ref.partition("://")
        parts = suffix.split("/")
        if len(parts) > 1:
            masked_last = "******"
            return f"{prefix}://{'/'.join(parts[:-1])}/{masked_last}"
        return f"{prefix}://******"
    # If arn
    if secret_ref.startswith("arn:"):
        parts = secret_ref.split(":")
        if len(parts) > 1:
            return f"{':'.join(parts[:-1])}:******"
    return "******"


class SourceConnectionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = SourceAuditService(session)

    async def connect_source(
        self,
        payload: SourceConnectionRequest,
        actor_id: UUID | None = None,
        actor_role: str = AuditActorRole.MERCHANT_OPERATOR.value,
    ) -> SourceConnectionResponse:
        # 1. Validate merchant exists
        merchant = await self.session.get(Merchant, payload.merchant_id)
        if not merchant:
            raise CatalogAuthorizationError(
                f"Merchant '{payload.merchant_id}' not found.",
                code="merchant_not_found",
            )

        # 2. Check slug uniqueness
        existing = await self.session.scalar(
            select(CatalogSource).where(CatalogSource.slug == payload.slug)
        )
        if existing:
            raise CatalogAuthorizationError(
                f"Catalog source with slug '{payload.slug}' already exists.",
                code="source_slug_conflict",
            )

        # 3. Create CatalogSource
        source = CatalogSource(
            merchant_id=payload.merchant_id,
            slug=payload.slug,
            name=payload.name,
            source_name=payload.name,
            kind=payload.source_type.lower(),
            source_type=payload.source_type,
            adapter_name=payload.adapter_name,
            adapter_version=payload.adapter_version,
            access_method=payload.access_method,
            credential_secret_ref=payload.credential_secret_ref,
            market_codes=payload.market_codes,
            category_codes=payload.category_codes,
            refresh_hours=payload.refresh_hours,
            source_status=CatalogSourceStatus.PENDING_REVIEW.value,
            operational_status=OperationalStatus.ENABLED.value,
            is_enabled=True,
        )
        self.session.add(source)
        await self.session.flush()

        # 4. Create default synchronization schedule
        interval_mins = max(15, min(10080, payload.refresh_hours * 60))
        schedule = CatalogSourceSchedule(
            source_id=source.id,
            merchant_id=source.merchant_id,
            enabled=True,
            sync_mode=SyncMode.INCREMENTAL.value,
            interval_minutes=interval_mins,
            timezone="UTC",
        )
        self.session.add(schedule)

        # 5. Log audit event
        await self.audit_service.log_event(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=source.merchant_id,
            source_id=source.id,
            entity_type="SOURCE",
            entity_id=str(source.id),
            action=AuditAction.SOURCE_CONNECTED.value,
            safe_change_summary={
                "slug": source.slug,
                "name": source.name,
                "adapter": source.adapter_name,
                "access_method": source.access_method,
                "masked_credential_ref": mask_credential_reference(source.credential_secret_ref),
            },
            outcome=AuditOutcome.SUCCESS.value,
        )

        await self.session.commit()
        await self.session.refresh(source)

        return SourceConnectionResponse(
            id=source.id,
            merchant_id=source.merchant_id,
            slug=source.slug,
            name=source.name,
            source_type=source.source_type or "MERCHANT_API",
            adapter_name=source.adapter_name,
            adapter_version=source.adapter_version,
            access_method=source.access_method,
            masked_credential_ref=mask_credential_reference(source.credential_secret_ref),
            source_status=source.source_status,
            operational_status=source.operational_status,
            is_enabled=source.is_enabled,
            created_at=source.created_at,
        )
