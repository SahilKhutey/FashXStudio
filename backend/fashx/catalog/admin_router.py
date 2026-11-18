from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_auth import (
    CatalogPermissionCode,
    TakedownReasonCode,
)
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
from fashx.core.database import get_db_session
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
