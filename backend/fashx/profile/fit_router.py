"""Authenticated FastAPI routes for Shopper Fit Profile (Phase 08.2)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from fashx.core.errors import ConsentRequiredError
from fashx.profile.consent import FitConsentService
from fashx.profile.fit_policy import UnsupportedCategoryPolicyError
from fashx.profile.fit_schemas import (
    CategoryFitPreferenceItem,
    CategoryPreferenceUpdateRequest,
    CategoryReadinessItem,
    ConsentPurpose,
    FitConsentStatusResponse,
    FitConsentUpdateRequest,
    FitProfileResponse,
    MeasurementBatchRequest,
    MeasurementDefinitionResponse,
    MeasurementHistoryItem,
    MeasurementUpdateRequest,
    PreferenceUpdateRequest,
    ShopperMeasurementResponse,
)
from fashx.profile.repositories.fit_profile_repository import (
    FitProfileRepository,
    OptimisticLockConflictError,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.profile.router import get_profile_uow
from fashx.profile.services.fit_profile_service import FitProfileService
from fashx.security.deps import Principal, get_principal
from fashx.security.errors import unauthorized

router = APIRouter(prefix="/profile/fit", tags=["fit-profile"])


def _principal_user_uuid(principal: Principal) -> UUID:
    try:
        return UUID(principal.user_id)
    except (ValueError, TypeError, AttributeError) as exc:
        raise unauthorized("Invalid authenticated principal user ID") from exc


def _build_service(uow: ProfileUnitOfWork) -> FitProfileService:
    return FitProfileService(
        repository=FitProfileRepository(uow.session),
        consent_service=FitConsentService(uow.session),
    )


@router.get("", response_model=FitProfileResponse)
async def get_fit_profile(
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> FitProfileResponse:
    """Retrieve authenticated shopper's fit profile and per-category policy readiness."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        resp = await service.get_profile(user_id)
        await uow.commit()
        return resp


@router.post(
    "/measurements",
    response_model=FitProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_fit_measurements(
    request: MeasurementBatchRequest,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> FitProfileResponse:
    """Add or record manual body measurements requiring FIT_PROFILE_STORAGE consent."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        try:
            resp = await service.add_measurements(user_id=user_id, batch=request)
            await uow.commit()
            return resp
        except ConsentRequiredError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc


@router.patch(
    "/measurements/{field}",
    response_model=ShopperMeasurementResponse,
)
async def update_fit_measurement(
    field: str,
    request: MeasurementUpdateRequest,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> ShopperMeasurementResponse:
    """Update a single measurement using optimistic concurrency (`expected_version`)."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        try:
            resp = await service.update_measurement(user_id=user_id, field=field, payload=request)
            await uow.commit()
            return resp
        except ConsentRequiredError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except OptimisticLockConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc


@router.post(
    "/measurements/{field}/confirm",
    response_model=ShopperMeasurementResponse,
)
async def confirm_fit_measurement(
    field: str,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> ShopperMeasurementResponse:
    """Confirm an existing or aged measurement remains current."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        try:
            resp = await service.confirm_measurement(user_id=user_id, field=field)
            await uow.commit()
            return resp
        except ConsentRequiredError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/measurements/{field}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_fit_measurement(
    field: str,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> None:
    """Delete a single measurement owned by the authenticated shopper."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        deleted = await service.delete_measurement(user_id=user_id, field=field)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Measurement '{field.upper()}' not found.",
            )
        await uow.commit()


@router.get(
    "/measurements/history",
    response_model=list[MeasurementHistoryItem],
)
async def list_measurement_history(
    field: str | None = Query(default=None, description="Optional field code filter"),
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> list[MeasurementHistoryItem]:
    """Retrieve owner-scoped measurement change history."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        return await service.get_history(user_id=user_id, field=field)


@router.put("/preferences", response_model=FitProfileResponse)
async def update_default_fit_preference(
    request: PreferenceUpdateRequest,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> FitProfileResponse:
    """Update subjective default fit preference without requiring body measurements."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        resp = await service.update_default_preference(
            user_id=user_id,
            default_fit_preference=request.default_fit_preference,
            preferred_unit=request.preferred_unit,
        )
        await uow.commit()
        return resp


@router.put(
    "/preferences/{category}",
    response_model=CategoryFitPreferenceItem,
)
async def update_category_fit_preference(
    category: str,
    request: CategoryPreferenceUpdateRequest,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> CategoryFitPreferenceItem:
    """Set subjective fit style preference for one garment category independently."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        try:
            resp = await service.update_category_preference(
                user_id=user_id,
                category=category,
                fit_preference=request.fit_preference,
            )
            await uow.commit()
            return resp
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc


@router.delete(
    "/preferences/{category}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_category_fit_preference(
    category: str,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> None:
    """Clear subjective fit preference for one category without affecting others."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        try:
            deleted = await service.delete_category_preference(user_id=user_id, category=category)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category preference for '{category.upper()}' not found.",
            )
        await uow.commit()


@router.get("/policies/{category}", response_model=CategoryReadinessItem)
async def get_category_fit_policy(
    category: str,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> CategoryReadinessItem:
    """Retrieve required vs optional measurement guidance for a category."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        try:
            return await service.get_category_policy_readiness(user_id=user_id, category=category)
        except UnsupportedCategoryPolicyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/definitions", response_model=list[MeasurementDefinitionResponse])
async def get_measurement_definitions(
    principal: Principal = Depends(get_principal),
) -> list[MeasurementDefinitionResponse]:
    """List plain-language shopper measurement explanations and tape positioning guidance."""
    _principal_user_uuid(principal)
    return FitProfileService.list_measurement_definitions()


@router.get("/consents", response_model=FitConsentStatusResponse)
async def get_fit_consents(
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> FitConsentStatusResponse:
    """Retrieve purpose-specific fit profile consent statuses."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        return await service.get_consent_status(user_id)


@router.put("/consents/{purpose}", response_model=FitConsentStatusResponse)
async def update_fit_consent(
    purpose: ConsentPurpose,
    request: FitConsentUpdateRequest,
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> FitConsentStatusResponse:
    """Grant or withdraw purpose-specific fit profile consent."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        try:
            resp = await service.update_consent(
                user_id=user_id,
                purpose=purpose,
                granted=request.granted,
                is_18_or_older=request.is_18_or_older,
                consent_version=request.consent_version or "2026.1",
            )
            await uow.commit()
            return resp
        except ConsentRequiredError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fit_profile(
    principal: Principal = Depends(get_principal),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> None:
    """Delete shopper's fit profile measurements, history, and preferences."""
    user_id = _principal_user_uuid(principal)
    async with uow:
        service = _build_service(uow)
        await service.delete_fit_profile(user_id)
        await uow.commit()
