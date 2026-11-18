from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_auth import (
    CatalogPermissionCode,
    TakedownReasonCode,
)
from database.models.catalog_sync import CatalogSyncCheckpoint, CatalogSyncRun
from fashx.catalog.acquisition.contracts_v2 import SourceHealthReport
from fashx.catalog.acquisition.health import SourceHealthChecker
from fashx.catalog.acquisition.registry import get_adapter_registry
from fashx.catalog.acquisition.schemas import (
    SyncCheckpointResponse,
    SyncRunResponse,
    SyncTriggerRequest,
)
from fashx.catalog.acquisition.sync_engine import CatalogSyncEngine
from fashx.catalog.authorization.schemas import (
    AuthorizationContext,
    AuthorizationDecisionResponse,
    EvidenceCreate,
    EvidenceResponse,
    PermissionCreate,
    PermissionResponse,
)
from fashx.catalog.authorization.service import CatalogAuthorizationService
from fashx.catalog.merchants.schemas import (
    MerchantCreate,
    MerchantResponse,
    MerchantVerificationRequest,
)
from fashx.catalog.merchants.service import MerchantService
from fashx.catalog.sources.schemas import (
    SourceCreate,
    SourceResponse,
    SourceStatusUpdate,
)
from fashx.catalog.sources.service import CatalogSourceService
from fashx.catalog.takedowns.schemas import (
    TakedownRequestCreate,
    TakedownResponse,
)
from fashx.catalog.takedowns.service import CatalogTakedownService
from fashx.core.database import get_db_session, get_session_factory
from fashx.security.deps import require_role

router = APIRouter(
    prefix="/admin/catalog",
    tags=["admin-catalog"],
    dependencies=[Depends(require_role("admin"))],
)


# --- Merchant Endpoints ---


@router.post("/merchants", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    payload: MerchantCreate,
    session: AsyncSession = Depends(get_db_session),
) -> MerchantResponse:
    service = MerchantService(session)
    merchant = await service.register_merchant(payload)
    await session.commit()
    return MerchantResponse.model_validate(merchant)


@router.get("/merchants/{merchant_id}", response_model=MerchantResponse)
async def get_merchant(
    merchant_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> MerchantResponse:
    service = MerchantService(session)
    merchant = await service.get_merchant(merchant_id)
    return MerchantResponse.model_validate(merchant)


@router.post("/merchants/{merchant_id}/verify", response_model=MerchantResponse)
async def verify_merchant(
    merchant_id: UUID,
    payload: MerchantVerificationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> MerchantResponse:
    service = MerchantService(session)
    merchant = await service.verify_merchant(merchant_id, payload)
    await session.commit()
    return MerchantResponse.model_validate(merchant)


# --- Source Endpoints ---


@router.post("/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> SourceResponse:
    service = CatalogSourceService(session)
    source = await service.register_source(payload)
    await session.commit()
    return SourceResponse.model_validate(source)


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> SourceResponse:
    service = CatalogSourceService(session)
    source = await service.get_source(source_id)
    return SourceResponse.model_validate(source)


@router.post("/sources/{source_id}/status", response_model=SourceResponse)
async def update_source_status(
    source_id: UUID,
    payload: SourceStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> SourceResponse:
    service = CatalogSourceService(session)
    source = await service.update_source_status(source_id, payload)
    await session.commit()
    return SourceResponse.model_validate(source)


@router.post(
    "/sources/{source_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_source_evidence(
    source_id: UUID,
    payload: EvidenceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> EvidenceResponse:
    if payload.source_id != source_id:
        payload = payload.model_copy(update={"source_id": source_id})
    service = CatalogAuthorizationService(session)
    evidence = await service.add_evidence(payload)
    await session.commit()
    return EvidenceResponse.model_validate(evidence)


@router.post(
    "/sources/{source_id}/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_source_permission(
    source_id: UUID,
    payload: PermissionCreate,
    session: AsyncSession = Depends(get_db_session),
) -> PermissionResponse:
    if payload.source_id != source_id:
        payload = payload.model_copy(update={"source_id": source_id})
    service = CatalogAuthorizationService(session)
    permission = await service.grant_permission(payload)
    await session.commit()
    return PermissionResponse.model_validate(permission)


@router.get("/sources/{source_id}/permissions", response_model=list[PermissionResponse])
async def list_source_permissions(
    source_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[PermissionResponse]:
    service = CatalogAuthorizationService(session)
    permissions = await service.list_permissions(source_id)
    return [PermissionResponse.model_validate(p) for p in permissions]


@router.post("/sources/{source_id}/suspend", response_model=SourceResponse)
async def suspend_source(
    source_id: UUID,
    reason: str = Query(..., min_length=3),
    session: AsyncSession = Depends(get_db_session),
) -> SourceResponse:
    service = CatalogSourceService(session)
    source = await service.suspend_source(source_id, reason)
    await session.commit()
    return SourceResponse.model_validate(source)


@router.post("/sources/{source_id}/resume", response_model=SourceResponse)
async def resume_source(
    source_id: UUID,
    reason: str = Query(..., min_length=3),
    session: AsyncSession = Depends(get_db_session),
) -> SourceResponse:
    service = CatalogSourceService(session)
    source = await service.resume_source(source_id, reason)
    await session.commit()
    return SourceResponse.model_validate(source)


@router.post(
    "/sources/{source_id}/takedown",
    response_model=TakedownResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_source_takedown(
    source_id: UUID,
    reason_code: TakedownReasonCode = Query(...),
    requested_by: str = Query(..., min_length=2),
    request_reference: str | None = Query(None),
    resolution_notes: str | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
) -> TakedownResponse:
    service = CatalogTakedownService(session)
    req = TakedownRequestCreate(
        source_id=source_id,
        reason_code=reason_code,
        requested_by=requested_by,
        request_reference=request_reference,
        resolution_notes=resolution_notes,
    )
    takedown = await service.initiate_takedown(req)
    await session.commit()
    return TakedownResponse.model_validate(takedown)


@router.get("/sources/{source_id}/authorization", response_model=AuthorizationDecisionResponse)
async def check_source_authorization(
    source_id: UUID,
    operation: CatalogPermissionCode = Query(...),
    product_id: str | None = Query(None),
    category: str | None = Query(None),
    market: str | None = Query(None),
    processor_id: str | None = Query(None),
    correlation_id: str | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
) -> AuthorizationDecisionResponse:
    service = CatalogAuthorizationService(session)
    context = AuthorizationContext(
        source_id=source_id,
        operation=operation.value,
        product_id=product_id,
        category=category,
        market=market,
        processor_id=processor_id,
        correlation_id=correlation_id,
    )
    decision = await service.evaluate(context)
    await session.commit()
    return decision


# --- Takedown Endpoints ---


@router.get("/takedowns/{request_id}", response_model=TakedownResponse)
async def get_takedown(
    request_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> TakedownResponse:
    service = CatalogTakedownService(session)
    takedown = await service.get_takedown(request_id)
    return TakedownResponse.model_validate(takedown)


# --- Health & Sync Endpoints ---


@router.get("/sources/{source_id}/health", response_model=SourceHealthReport)
async def get_source_health(
    source_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> SourceHealthReport:
    """Evaluate current health state of a catalog source based on recent syncs and status."""
    return await SourceHealthChecker.evaluate_health(session, source_id)


@router.post("/sources/{source_id}/health-check", response_model=SourceHealthReport)
async def check_source_health(
    source_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> SourceHealthReport:
    """Trigger a live diagnostic probe for an authorized catalog source."""
    src_res = await session.execute(select(CatalogSource).where(CatalogSource.id == source_id))
    source = src_res.scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found.",
        )

    probe_func = None
    registry = get_adapter_registry()
    if source.slug in registry.list_sources():
        adapter = registry.get(source.slug)
        if hasattr(adapter, "health_check"):

            async def _probe():
                return await adapter.health_check()

            probe_func = _probe

    return await SourceHealthChecker.perform_probe(session, source_id, probe=probe_func)


@router.post(
    "/sources/{source_id}/sync",
    response_model=SyncRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_source_sync(
    source_id: UUID,
    payload: SyncTriggerRequest = SyncTriggerRequest(),
    session: AsyncSession = Depends(get_db_session),
) -> SyncRunResponse:
    """Execute synchronization (full or incremental) for an authorized catalog source."""
    src_res = await session.execute(select(CatalogSource).where(CatalogSource.id == source_id))
    source = src_res.scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found.",
        )

    registry = get_adapter_registry()
    if source.slug not in registry.list_sources():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No adapter registered for source slug '{source.slug}'.",
        )

    adapter = registry.get(source.slug)
    engine = CatalogSyncEngine(get_session_factory())
    await engine.execute_sync(
        source_id=source_id,
        adapter=adapter,
        mode=payload.mode,
        limit_per_page=payload.limit_per_page,
        apply=payload.apply,
    )

    latest_run_res = await session.execute(
        select(CatalogSyncRun)
        .where(CatalogSyncRun.source_id == source_id)
        .order_by(CatalogSyncRun.started_at.desc())
        .limit(1)
    )
    latest_run = latest_run_res.scalar_one()
    return SyncRunResponse.model_validate(latest_run)


@router.get("/sources/{source_id}/sync-runs", response_model=list[SyncRunResponse])
async def list_source_sync_runs(
    source_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> list[SyncRunResponse]:
    """List historical and active sync runs for a source."""
    stmt = (
        select(CatalogSyncRun)
        .where(CatalogSyncRun.source_id == source_id)
        .order_by(CatalogSyncRun.started_at.desc())
        .limit(limit)
    )
    res = await session.execute(stmt)
    runs = res.scalars().all()
    return [SyncRunResponse.model_validate(r) for r in runs]


@router.get("/sources/{source_id}/checkpoints", response_model=list[SyncCheckpointResponse])
async def list_source_checkpoints(
    source_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[SyncCheckpointResponse]:
    """List durable synchronization checkpoints for a source."""
    stmt = (
        select(CatalogSyncCheckpoint)
        .where(CatalogSyncCheckpoint.source_id == source_id)
        .order_by(CatalogSyncCheckpoint.updated_at.desc())
    )
    res = await session.execute(stmt)
    checkpoints = res.scalars().all()
    return [SyncCheckpointResponse.model_validate(c) for c in checkpoints]


@router.get("/sync-runs/{run_id}", response_model=SyncRunResponse)
async def get_sync_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> SyncRunResponse:
    """Retrieve details of a specific sync run execution."""
    res = await session.execute(select(CatalogSyncRun).where(CatalogSyncRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync run '{run_id}' not found.",
        )
    return SyncRunResponse.model_validate(run)
