"""Authenticated FastAPI routes for Phase 08.3 Fit Recommendations & Feedback."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from database.models.catalog import CatalogSource, MerchantOffer, MerchantProduct
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.router import get_catalog_uow
from fashx.catalog.size_charts.service import SizeChartService
from fashx.fit.contracts import (
    FitFeedbackCreateRequest,
    FitFeedbackResponse,
    FitRecommendationRequest,
    FitRecommendationResult,
    MeasurementValue,
)
from fashx.fit.enums import FitPreference
from fashx.fit.feedback import FitFeedbackService
from fashx.fit.repository import DuplicateFitFeedbackError, FitRecommendationRepository
from fashx.fit.service import FitEvidenceSecurityError, FitRecommendationService
from fashx.profile.consent import FitConsentService
from fashx.profile.fit_schemas import ConsentPurpose
from fashx.profile.repositories.fit_profile_repository import FitProfileRepository
from fashx.security.deps import Principal, get_principal
from fashx.security.errors import unauthorized

router = APIRouter(prefix="/fit", tags=["fit-recommendations"])


def _principal_user_uuid(principal: Principal) -> UUID:
    try:
        return UUID(principal.user_id)
    except (ValueError, TypeError, AttributeError) as exc:
        raise unauthorized("Invalid authenticated principal user ID") from exc


def _parse_uuid(value: UUID | str, label: str) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid UUID for {label}.",
        ) from exc


@router.post(
    "/recommendations",
    response_model=FitRecommendationResult,
)
async def evaluate_fit_recommendation(
    payload: FitRecommendationRequest,
    principal: Principal = Depends(get_principal),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Evaluate product size guidance exclusively from server-resolved profile and chart evidence."""
    user_id = _principal_user_uuid(principal)
    product_uuid = _parse_uuid(payload.product_id, "product_id")
    offer_uuid = (
        _parse_uuid(payload.merchant_offer_id, "merchant_offer_id")
        if payload.merchant_offer_id is not None
        else None
    )

    async with catalog_uow:
        garment = await catalog_uow.canonical_garments.get_by_id(product_uuid)
        if garment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{payload.product_id}' not found.",
            )

        selected_offer: MerchantOffer | None = None
        if offer_uuid is not None:
            selected_offer = await catalog_uow.session.get(MerchantOffer, offer_uuid)
            if selected_offer is None or selected_offer.garment_id != garment.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Merchant offer '{payload.merchant_offer_id}' not found for product.",
                )
        else:
            offers = await catalog_uow.offers.list_for_garment(garment.id)
            for off in offers:
                if off.status == "ACTIVE" and off.takedown_status == "NONE":
                    selected_offer = off
                    break

        if not garment.active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{payload.product_id}' is inactive.",
            )

        # Resolve merchant product, source permissions, and takedown status
        merchant_id: UUID | None = selected_offer.merchant_id if selected_offer else None
        merchant_product_id: UUID | None = (
            selected_offer.merchant_product_id if selected_offer else None
        )
        permissions_valid = True
        source_perm_rev: int | None = None

        if selected_offer is not None:
            if selected_offer.status != "ACTIVE" or selected_offer.takedown_status != "NONE":
                permissions_valid = False
            if selected_offer.source_id is not None:
                source = await catalog_uow.session.get(CatalogSource, selected_offer.source_id)
                if source is not None:
                    source_perm_rev = source.permission_revision
                    if not source.is_enabled or source.source_status == "SUSPENDED":
                        permissions_valid = False
            if merchant_product_id is not None:
                mprod = await catalog_uow.session.get(MerchantProduct, merchant_product_id)
                if mprod is not None and mprod.takedown_status != "NONE":
                    permissions_valid = False

        # Server-side resolution of shopper profile, measurements, preferences, and consent
        profile_repo = FitProfileRepository(catalog_uow.session)
        consent_svc = FitConsentService(catalog_uow.session)

        storage_consent = await consent_svc.has_consent(user_id, ConsentPurpose.FIT_PROFILE_STORAGE)
        rec_consent = await consent_svc.has_consent(
            user_id, ConsentPurpose.FIT_RECOMMENDATION_PROCESSING
        )
        consent_ok = storage_consent and rec_consent

        prof = await profile_repo.get_or_create_profile(user_id)
        raw_measurements = await profile_repo.list_measurements(user_id)
        shopper_map: dict[str, MeasurementValue] = {}
        max_rev = 1
        for rec in raw_measurements:
            if rec.status in ("DELETED", "REVOKED"):
                continue
            val = rec.normalized_value if rec.normalized_value is not None else Decimal(str(rec.value))
            orig = rec.original_value if rec.original_value is not None else val
            m_at = rec.measured_at or rec.created_at or datetime.now(UTC)
            if m_at.tzinfo is None:
                m_at = m_at.replace(tzinfo=UTC)
            max_rev = max(max_rev, int(rec.version))
            shopper_map[rec.measurement_type.upper()] = MeasurementValue(
                field=rec.measurement_type.upper(),
                value_cm=val,
                original_value=orig,
                original_unit=rec.original_unit or rec.unit or "CM",
                measured_at=m_at,
                revision=int(rec.version),
                provenance="VERIFIED_SOURCE" if rec.verified_at else "SHOPPER_ENTERED",
                status=rec.status,
            )

        category = payload.category or garment.category
        cat_pref_rec = await profile_repo.get_category_preference(user_id, category.strip().upper())
        raw_pref = cat_pref_rec.preferred_fit if cat_pref_rec else prof.preferred_fit
        try:
            fit_pref = FitPreference(str(raw_pref).upper())
        except ValueError:
            fit_pref = FitPreference.NO_PREFERENCE

        # Server-side resolution of product size chart and variant availability
        chart = None
        availability = None
        if merchant_product_id is not None:
            sc_service = SizeChartService(catalog_uow.session)
            chart = await sc_service.get_product_size_chart(merchant_product_id=merchant_product_id)
            availability = await sc_service.get_variant_availability(
                merchant_product_id=merchant_product_id
            )

        fit_service = FitRecommendationService(catalog_uow.session)
        try:
            result = await fit_service.evaluate_recommendation(
                shopper_id=user_id,
                product_id=garment.id,
                merchant_offer_id=selected_offer.id if selected_offer else None,
                merchant_id=merchant_id,
                merchant_product_id=merchant_product_id,
                category=category,
                shopper_measurements=shopper_map,
                shopper_measurement_revision=max_rev if shopper_map else None,
                consent_verified=consent_ok,
                permissions_valid=permissions_valid,
                source_permission_revision=source_perm_rev,
                fit_preference=fit_pref,
                fit_preference_revision=prof.version,
                chart=chart,
                availability=availability,
            )
            await catalog_uow.commit()
            return result
        except FitEvidenceSecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=FitRecommendationResult,
)
async def get_fit_recommendation(
    recommendation_id: UUID,
    principal: Principal = Depends(get_principal),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Retrieve a stored fit recommendation snapshot for the authenticated owner."""
    user_id = _principal_user_uuid(principal)
    async with catalog_uow:
        service = FitRecommendationService(catalog_uow.session)
        try:
            return await service.get_stored_recommendation(
                recommendation_id=recommendation_id, shopper_id=user_id
            )
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/recommendations/{recommendation_id}/feedback",
    response_model=FitFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_fit_feedback(
    recommendation_id: UUID,
    payload: FitFeedbackCreateRequest,
    principal: Principal = Depends(get_principal),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Submit shopper fit feedback linked strictly to an owned recommendation snapshot."""
    user_id = _principal_user_uuid(principal)
    async with catalog_uow:
        fb_service = FitFeedbackService(FitRecommendationRepository(catalog_uow.session))
        try:
            resp = await fb_service.submit(
                shopper_id=user_id,
                recommendation_id=recommendation_id,
                payload=payload,
            )
            await catalog_uow.commit()
            return resp
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except DuplicateFitFeedbackError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/recommendations/{recommendation_id}/feedback",
    response_model=FitFeedbackResponse,
)
async def get_fit_feedback(
    recommendation_id: UUID,
    principal: Principal = Depends(get_principal),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Retrieve the authenticated shopper's submitted feedback for a recommendation."""
    user_id = _principal_user_uuid(principal)
    async with catalog_uow:
        fb_service = FitFeedbackService(FitRecommendationRepository(catalog_uow.session))
        try:
            return await fb_service.get_own_feedback(
                shopper_id=user_id,
                recommendation_id=recommendation_id,
            )
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
