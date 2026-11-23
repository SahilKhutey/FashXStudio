from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_operations import AuditActorRole
from fashx.catalog.operations.image_permission_status_service import (
    ImagePermissionStatusService,
)
from fashx.catalog.operations.ingestion_report_service import IngestionReportService
from fashx.catalog.operations.manual_sync_service import ManualSyncService
from fashx.catalog.operations.merchant_product_removal_service import (
    MerchantProductRemovalService,
)
from fashx.catalog.operations.merchant_product_update_service import (
    MerchantProductUpdateService,
)
from fashx.catalog.operations.rejection_report_service import RejectionReportService
from fashx.catalog.operations.schemas import (
    CatalogAuditEventResponse,
    CatalogAuditListResponse,
    ImagePermissionMatrixResponse,
    IngestErrorListResponse,
    ManualSyncRequest,
    ManualSyncResponse,
    MerchantOfferDeactivateRequest,
    MerchantOfferDeactivateResponse,
    MerchantProductOverrideRequest,
    MerchantProductOverrideResponse,
    QuarantineReportListResponse,
    SourceConnectionRequest,
    SourceConnectionResponse,
    SourceOperationalStatusRequest,
    SourceOperationalStatusResponse,
    SourceScheduleRequest,
    SourceScheduleResponse,
    SourceTakedownRequest,
    SourceTakedownResponse,
    SyncStatusDashboardResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService
from fashx.catalog.operations.source_connection_service import SourceConnectionService
from fashx.catalog.operations.source_lifecycle_service import SourceLifecycleService
from fashx.catalog.operations.source_takedown_service import SourceTakedownService
from fashx.catalog.operations.sync_schedule_service import SyncScheduleService
from fashx.catalog.operations.sync_status_service import SyncStatusService
from fashx.core.database import get_db_session
from fashx.security.deps import Principal, get_principal, require_role

router = APIRouter()


def get_current_merchant_id(
    x_merchant_id: str | None = Header(None, alias="X-Merchant-ID"),
    principal: Principal = Depends(get_principal),
) -> UUID:
    if x_merchant_id:
        try:
            return UUID(x_merchant_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid X-Merchant-ID header format: {x_merchant_id}",
            )
    try:
        return UUID(principal.user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Merchant identity not identified. Provide X-Merchant-ID header.",
        )


# ============================================================================
# Merchant Operational Endpoints (/api/v1/merchant/...)
# ============================================================================


@router.post(
    "/merchant/sources",
    response_model=SourceConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Merchant Catalog Operations"],
)
async def connect_merchant_source(
    payload: SourceConnectionRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SourceConnectionResponse:
    """Register and connect an authorized catalog source."""
    if not principal.is_admin and payload.merchant_id != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot connect a catalog source for another merchant.",
        )
    svc = SourceConnectionService(session)
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass
    actor_role = (
        AuditActorRole.PLATFORM_ADMIN.value
        if principal.is_admin
        else AuditActorRole.MERCHANT_OPERATOR.value
    )
    return await svc.connect_source(payload, actor_id=actor_id, actor_role=actor_role)


@router.get(
    "/merchant/sources/{source_id}/status",
    response_model=SyncStatusDashboardResponse,
    tags=["Merchant Catalog Operations"],
)
async def get_source_sync_status(
    source_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SyncStatusDashboardResponse:
    """Retrieve operational health, counts, and last synchronization outcome."""
    svc = SyncStatusService(session)
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.get_source_sync_status(source_id, merchant_id=scoped_merchant)


@router.patch(
    "/merchant/sources/{source_id}/operational-status",
    response_model=SourceOperationalStatusResponse,
    tags=["Merchant Catalog Operations"],
)
async def update_source_operational_status(
    source_id: UUID,
    payload: SourceOperationalStatusRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SourceOperationalStatusResponse:
    """Toggle source operational status (ENABLE, DISABLE, PAUSE)."""
    svc = SourceLifecycleService(session)
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass
    actor_role = (
        AuditActorRole.PLATFORM_ADMIN.value
        if principal.is_admin
        else AuditActorRole.MERCHANT_OPERATOR.value
    )
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.update_operational_status(
        source_id,
        payload,
        actor_id=actor_id,
        actor_role=actor_role,
        merchant_id=scoped_merchant,
    )


@router.post(
    "/merchant/sources/{source_id}/sync",
    response_model=ManualSyncResponse,
    tags=["Merchant Catalog Operations"],
)
async def trigger_manual_source_sync(
    source_id: UUID,
    payload: ManualSyncRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ManualSyncResponse:
    """Trigger manual synchronization with idempotency guarantee."""
    svc = ManualSyncService(session)
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass
    actor_role = (
        AuditActorRole.PLATFORM_ADMIN.value
        if principal.is_admin
        else AuditActorRole.MERCHANT_OPERATOR.value
    )
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.trigger_sync(
        source_id,
        payload,
        actor_id=actor_id,
        actor_role=actor_role,
        merchant_id=scoped_merchant,
    )


@router.get(
    "/merchant/sources/{source_id}/schedule",
    response_model=SourceScheduleResponse,
    tags=["Merchant Catalog Operations"],
)
async def get_source_schedule(
    source_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SourceScheduleResponse:
    """Retrieve synchronization schedule and cadence."""
    svc = SyncScheduleService(session)
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.get_schedule(source_id, merchant_id=scoped_merchant)


@router.put(
    "/merchant/sources/{source_id}/schedule",
    response_model=SourceScheduleResponse,
    tags=["Merchant Catalog Operations"],
)
async def update_source_schedule(
    source_id: UUID,
    payload: SourceScheduleRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SourceScheduleResponse:
    """Configure synchronization schedule (intervals >= 15m)."""
    svc = SyncScheduleService(session)
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass
    actor_role = (
        AuditActorRole.PLATFORM_ADMIN.value
        if principal.is_admin
        else AuditActorRole.MERCHANT_OPERATOR.value
    )
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.update_schedule(
        source_id,
        payload,
        actor_id=actor_id,
        actor_role=actor_role,
        merchant_id=scoped_merchant,
    )


@router.get(
    "/merchant/sources/{source_id}/errors",
    response_model=IngestErrorListResponse,
    tags=["Merchant Catalog Operations"],
)
async def get_source_ingestion_errors(
    source_id: UUID,
    run_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> IngestErrorListResponse:
    """Retrieve structured, sanitized error report for ingestion failures."""
    svc = IngestionReportService(session)
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.get_errors(
        source_id=source_id,
        run_id=run_id,
        merchant_id=scoped_merchant,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/merchant/sources/{source_id}/quarantine",
    response_model=QuarantineReportListResponse,
    tags=["Merchant Catalog Operations"],
)
async def get_source_quarantined_products(
    source_id: UUID,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> QuarantineReportListResponse:
    """Retrieve quarantined records with actionable resolution guidance."""
    svc = RejectionReportService(session)
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.get_rejection_report(
        source_id=source_id,
        status=status_filter,
        merchant_id=scoped_merchant,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/merchant/sources/{source_id}/image-permissions",
    response_model=ImagePermissionMatrixResponse,
    tags=["Merchant Catalog Operations"],
)
async def get_source_image_permission_matrix(
    source_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ImagePermissionMatrixResponse:
    """Retrieve granular image and VTO permission matrix and asset counts."""
    svc = ImagePermissionStatusService(session)
    scoped_merchant = None if principal.is_admin else merchant_id
    return await svc.get_image_permission_matrix(source_id, merchant_id=scoped_merchant)


@router.post(
    "/merchant/products/{product_id}/override",
    response_model=MerchantProductOverrideResponse,
    tags=["Merchant Catalog Operations"],
)
async def override_merchant_product_field(
    product_id: UUID,
    payload: MerchantProductOverrideRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> MerchantProductOverrideResponse:
    """Apply permitted field overrides to a merchant-owned product."""
    svc = MerchantProductUpdateService(session)
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass
    actor_role = (
        AuditActorRole.PLATFORM_ADMIN.value
        if principal.is_admin
        else AuditActorRole.MERCHANT_OPERATOR.value
    )
    return await svc.apply_product_override(
        product_id,
        payload,
        merchant_id=merchant_id,
        actor_id=actor_id,
        actor_role=actor_role,
    )


@router.post(
    "/merchant/offers/{offer_id}/deactivate",
    response_model=MerchantOfferDeactivateResponse,
    tags=["Merchant Catalog Operations"],
)
async def deactivate_merchant_offer(
    offer_id: UUID,
    payload: MerchantOfferDeactivateRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> MerchantOfferDeactivateResponse:
    """Deactivate merchant offer while preserving shared canonical garment."""
    svc = MerchantProductRemovalService(session)
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass
    actor_role = (
        AuditActorRole.PLATFORM_ADMIN.value
        if principal.is_admin
        else AuditActorRole.MERCHANT_OPERATOR.value
    )
    return await svc.deactivate_offer(
        offer_id,
        payload,
        merchant_id=merchant_id,
        actor_id=actor_id,
        actor_role=actor_role,
    )


@router.get(
    "/merchant/audit",
    response_model=CatalogAuditListResponse,
    tags=["Merchant Catalog Operations"],
)
async def get_merchant_audit_trail(
    source_id: UUID | None = Query(None),
    entity_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    merchant_id: UUID = Depends(get_current_merchant_id),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> CatalogAuditListResponse:
    """Retrieve immutable audit trail scoped to the merchant."""
    svc = SourceAuditService(session)
    scoped_merchant = None if principal.is_admin else merchant_id
    events, total = await svc.get_audit_events(
        merchant_id=scoped_merchant,
        source_id=source_id,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )
    return CatalogAuditListResponse(
        events=[CatalogAuditEventResponse.model_validate(e) for e in events],
        total_count=total,
    )


# ============================================================================
# Platform Admin Operational Endpoints (/api/v1/admin/...)
# ============================================================================


@router.post(
    "/admin/sources/{source_id}/takedown",
    response_model=SourceTakedownResponse,
    dependencies=[Depends(require_role("admin"))],
    tags=["Admin Catalog Operations"],
)
async def execute_source_takedown(
    source_id: UUID,
    payload: SourceTakedownRequest,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SourceTakedownResponse:
    """Execute immediate emergency takedown of a catalog source."""
    svc = SourceTakedownService(session)
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass
    return await svc.execute_takedown(
        source_id,
        payload,
        actor_id=actor_id,
        actor_role=AuditActorRole.PLATFORM_ADMIN.value,
    )
