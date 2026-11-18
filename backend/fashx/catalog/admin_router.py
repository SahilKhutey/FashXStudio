from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, IngestRun
from database.models.catalog_auth import (
    CatalogPermissionCode,
    TakedownReasonCode,
)
from database.models.catalog_sync import (
    CatalogSyncCheckpoint,
    CatalogSyncRun,
)
from fashx.catalog.acquisition.contracts_v2 import SourceHealthReport, SyncMode
from fashx.catalog.acquisition.health import SourceHealthChecker
from fashx.catalog.acquisition.quarantine import CatalogQuarantineService
from fashx.catalog.acquisition.registry import get_adapter_registry
from fashx.catalog.acquisition.schemas import (
    IngestionJobCreateRequest,
    IngestionJobReportResponse,
    IngestionJobResponse,
    QuarantineListResponse,
    QuarantineRecordResponse,
    QuarantineReprocessResponse,
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


# =========================================================================
# Workstream 5.3: Catalog Ingestion Jobs & Quarantine Endpoints
# =========================================================================


@router.post(
    "/ingestion-jobs",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ingestion_job(
    payload: IngestionJobCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobResponse:
    """Create and trigger a catalog ingestion job."""
    res = await session.execute(select(CatalogSource).where(CatalogSource.id == payload.source_id))
    source = res.scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog source '{payload.source_id}' not found.",
        )

    session_factory = get_session_factory()
    sync_engine = CatalogSyncEngine(session_factory)
    registry = get_adapter_registry()
    adapter = registry.get(source.slug)

    sync_mode = SyncMode.FULL if payload.mode.lower() == "full" else SyncMode.INCREMENTAL
    report = await sync_engine.execute_sync(
        source_id=source.id,
        adapter=adapter,
        mode=sync_mode,
        limit_per_page=payload.limit_per_page,
        apply=not payload.dry_run,
    )

    if not report.ingest_run_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingestion run was not recorded.",
        )

    run_res = await session.execute(select(IngestRun).where(IngestRun.id == report.ingest_run_id))
    run = run_res.scalar_one()
    return IngestionJobResponse.model_validate(run)


@router.get("/ingestion-jobs/{run_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(
    run_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobResponse:
    """Retrieve status and metadata for an ingestion job."""
    res = await session.execute(select(IngestRun).where(IngestRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{run_id}' not found.",
        )
    return IngestionJobResponse.model_validate(run)


@router.get("/ingestion-jobs/{run_id}/report", response_model=IngestionJobReportResponse)
async def get_ingestion_job_report(
    run_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobReportResponse:
    """Retrieve detailed outcome counts, errors, and image processing summary for an ingestion run."""
    res = await session.execute(select(IngestRun).where(IngestRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{run_id}' not found.",
        )

    counts = run.counts or {}
    rejection_reasons = counts.get("rejection_reasons", {})
    image_counts = counts.get("image_counts", {})

    return IngestionJobReportResponse(
        run_id=run.id,
        source_id=run.source_id,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        counts=counts,
        rejection_reasons=rejection_reasons,
        image_counts=image_counts,
        error=run.error,
    )


@router.post("/ingestion-jobs/{run_id}/cancel", response_model=IngestionJobResponse)
async def cancel_ingestion_job(
    run_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobResponse:
    """Cancel / abort an active ingestion job."""
    res = await session.execute(select(IngestRun).where(IngestRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{run_id}' not found.",
        )

    if run.status in {"COMPLETED", "FAILED", "REJECTED", "ABORTED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job in terminal state '{run.status}'.",
        )

    run.status = "ABORTED"
    await session.commit()
    await session.refresh(run)
    return IngestionJobResponse.model_validate(run)


@router.get("/quarantine", response_model=QuarantineListResponse)
async def list_quarantine_records(
    source_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> QuarantineListResponse:
    """List quarantined product records with optional source and status filters."""
    service = CatalogQuarantineService(session)
    items, total = await service.list_quarantine(
        source_id=source_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return QuarantineListResponse(
        items=[QuarantineRecordResponse.model_validate(it) for it in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/quarantine/{quarantine_id}", response_model=QuarantineRecordResponse)
async def get_quarantine_record(
    quarantine_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> QuarantineRecordResponse:
    """Retrieve details of a single quarantined product record."""
    service = CatalogQuarantineService(session)
    record = await service.get_by_id(quarantine_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quarantine record '{quarantine_id}' not found.",
        )
    return QuarantineRecordResponse.model_validate(record)


@router.post(
    "/quarantine/{quarantine_id}/reprocess",
    response_model=QuarantineReprocessResponse,
)
async def reprocess_quarantine_record(
    quarantine_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> QuarantineReprocessResponse:
    """Trigger reprocessing of a quarantined product record."""
    service = CatalogQuarantineService(session)
    record = await service.get_by_id(quarantine_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quarantine record '{quarantine_id}' not found.",
        )

    # Reprocess through pipeline
    await service.mark_reprocessed(quarantine_id, note="Reprocessed via admin API")
    await session.commit()

    return QuarantineReprocessResponse(
        id=record.id,
        status="REPROCESSED",
        message="Quarantine record marked as reprocessed.",
    )
