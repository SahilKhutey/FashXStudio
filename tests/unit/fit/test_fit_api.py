"""Tests for Phase 08.3 Fit Recommendation FastAPI Routes, Mounting & Security."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from fashx.catalog.size_charts.enums import (
    MeasurementBasis as CatBasis,
)
from fashx.catalog.size_charts.enums import (
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.schemas import (
    ProductSizeChartResponse,
    SizeChartRowResponse,
    SizeMeasurementResponse,
    SizeSystemRef,
    SourceProvenance,
)
from fashx.fit.contracts import FitFeedbackCreateRequest, FitRecommendationRequest
from fashx.fit.enums import FitFeedbackReason, RecommendationStatus
from fashx.fit.repository import FitRecommendationRepository
from fashx.fit.router import (
    evaluate_fit_recommendation,
    get_fit_feedback,
    get_fit_recommendation,
    submit_fit_feedback,
)
from fashx.main import app
from fashx.profile.fit_schemas import ConsentPurpose
from fashx.security.deps import Principal


def _chart(*, merchant_id: str, merchant_product_id: str) -> ProductSizeChartResponse:
    return ProductSizeChartResponse(
        chart_id=f"chart-{merchant_id}",
        merchant_product_id=merchant_product_id,
        merchant_id=merchant_id,
        version=4,
        content_fingerprint="abc123",
        size_system=SizeSystemRef(code="INTL_ALPHA", display_name="INTL"),
        measurement_basis=CatBasis.BODY,
        display_unit=MeasurementUnit.CM,
        status=SizeChartStatus.AVAILABLE,
        is_stale=False,
        provenance=SourceProvenance(source_id=f"src-{merchant_id}", source_revision="rev-9"),
        rows=[
            SizeChartRowResponse(
                merchant_size="S",
                measurements=[
                    SizeMeasurementResponse(
                        field_code="CHEST",
                        display_name="Chest",
                        value=Decimal("90"),
                        unit=MeasurementUnit.CM,
                        normalized_cm=Decimal("90"),
                    )
                ],
            ),
            SizeChartRowResponse(
                merchant_size="M",
                measurements=[
                    SizeMeasurementResponse(
                        field_code="CHEST",
                        display_name="Chest",
                        value=Decimal("96"),
                        unit=MeasurementUnit.CM,
                        normalized_cm=Decimal("96"),
                    )
                ],
            ),
        ],
        last_verified_at=datetime.now(UTC),
    )


def _run(coro):
    stack = [coro]
    val = None
    while stack:
        curr = stack[-1]
        try:
            if inspect.iscoroutine(curr):
                nxt = curr.send(val)
                val = None
                if inspect.iscoroutine(nxt):
                    stack.append(nxt)
            else:
                stack.pop()
        except StopIteration as e:
            val = e.value
            stack.pop()
        except Exception as exc:
            stack.pop()
            while stack:
                try:
                    nxt = stack[-1].throw(exc)
                    if inspect.iscoroutine(nxt):
                        stack.append(nxt)
                    exc = None
                    break
                except StopIteration as e:
                    val = e.value
                    stack.pop()
                    exc = None
                    break
                except Exception as exc2:
                    exc = exc2
                    stack.pop()
            if exc is not None:
                raise exc
    return val


class _FakeRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _FakeSession:
    def __init__(self, objects: dict):
        self._objects = objects

    async def get(self, model_cls, key):
        return self._objects.get((model_cls.__name__, key))


class _FakeRepo:
    def __init__(self, items):
        self._items = items

    async def get_by_id(self, key):
        return self._items.get(key)

    async def list_for_garment(self, garment_id):
        return [v for v in self._items.values() if getattr(v, "garment_id", None) == garment_id]


class _FakeCatalogUoW:
    def __init__(self, session, garments, offers):
        self.session = session
        self.canonical_garments = _FakeRepo(garments)
        self.offers = _FakeRepo(offers)
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self):
        self.committed = True


def test_fit_routes_mounted_with_authentication() -> None:
    spec_paths = app.openapi()["paths"]
    assert "/api/v1/fit/recommendations" in spec_paths
    assert "post" in spec_paths["/api/v1/fit/recommendations"]
    assert "/api/v1/fit/recommendations/{recommendation_id}" in spec_paths
    assert "get" in spec_paths["/api/v1/fit/recommendations/{recommendation_id}"]
    assert "/api/v1/fit/recommendations/{recommendation_id}/feedback" in spec_paths
    assert "post" in spec_paths["/api/v1/fit/recommendations/{recommendation_id}/feedback"]
    assert "get" in spec_paths["/api/v1/fit/recommendations/{recommendation_id}/feedback"]

    from fashx.security.deps import get_principal

    matching_routes = [
        r
        for r in app.routes
        if hasattr(r, "path") and "/api/v1/fit/recommendations" in str(r.path)
    ]
    if matching_routes:
        for route in matching_routes:
            deps = {
                getattr(d, "dependency", None)
                for d in getattr(route, "dependencies", ())
            }
            assert get_principal in deps or any(
                d is get_principal
                for dep in getattr(getattr(route, "dependant", None), "dependencies", ())
                for d in (getattr(dep, "call", None),)
            )


def test_fit_request_forbids_client_supplied_trusted_fields() -> None:
    # Client must not pass authoritative measurements, confidence, or shopper_id
    with pytest.raises(ValidationError):
        FitRecommendationRequest.model_validate(
            {
                "product_id": str(uuid4()),
                "shopper_id": str(uuid4()),
                "confidence": 0.99,
            }
        )


def test_fit_api_end_to_end_flow_and_ownership() -> None:
    user_a = uuid4()
    user_b = uuid4()
    garment_id = uuid4()
    offer_id = uuid4()
    merchant_id = uuid4()
    mprod_id = uuid4()

    principal_a = Principal(user_id=str(user_a), subject=str(user_a), roles=frozenset({"shopper"}))
    principal_b = Principal(user_id=str(user_b), subject=str(user_b), roles=frozenset({"shopper"}))

    garment = _FakeRecord(id=garment_id, category="TSHIRTS", active=True)
    offer = _FakeRecord(
        id=offer_id,
        garment_id=garment_id,
        merchant_id=merchant_id,
        merchant_product_id=mprod_id,
        source_id=None,
        status="ACTIVE",
        takedown_status="NONE",
    )
    mprod = _FakeRecord(id=mprod_id, takedown_status="NONE")
    fake_session = _FakeSession(
        {
            ("MerchantOffer", offer_id): offer,
            ("MerchantProduct", mprod_id): mprod,
        }
    )
    uow = _FakeCatalogUoW(fake_session, {garment_id: garment}, {offer_id: offer})

    shared_rec_repo = FitRecommendationRepository(None)

    class _MockProfileRepo:
        def __init__(self, _sess):
            pass

        async def get_or_create_profile(self, uid):
            return _FakeRecord(user_id=uid, preferred_fit="REGULAR", version=1)

        async def list_measurements(self, _uid):
            return [
                _FakeRecord(
                    measurement_type="CHEST",
                    normalized_value=Decimal("96"),
                    original_value=Decimal("96"),
                    original_unit="CM",
                    unit="CM",
                    value=96.0,
                    measured_at=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                    verified_at=None,
                    version=2,
                    status="ACTIVE",
                )
            ]

        async def get_category_preference(self, _uid, _cat):
            return None

    class _MockConsentSvc:
        def __init__(self, _sess):
            pass

        async def has_consent(self, _uid, purpose):
            return purpose in (
                ConsentPurpose.FIT_PROFILE_STORAGE,
                ConsentPurpose.FIT_RECOMMENDATION_PROCESSING,
            )

    class _MockChartSvc:
        def __init__(self, _sess):
            pass

        async def get_product_size_chart(self, **_kw):
            c = _chart(merchant_id=str(merchant_id), merchant_product_id=str(mprod_id))
            # Point measurement (chest=96) on Size M matches CHEST=96
            return c

        async def get_variant_availability(self, **_kw):
            return None

    with (
        patch("fashx.fit.router.FitProfileRepository", _MockProfileRepo),
        patch("fashx.fit.router.FitConsentService", _MockConsentSvc),
        patch("fashx.fit.router.SizeChartService", _MockChartSvc),
        patch(
            "fashx.fit.router.FitRecommendationService",
            lambda _s: __import__(
                "fashx.fit.service", fromlist=["FitRecommendationService"]
            ).FitRecommendationService(repository=shared_rec_repo),
        ),
        patch("fashx.fit.router.FitRecommendationRepository", lambda _s: shared_rec_repo),
    ):
        res = _run(
            evaluate_fit_recommendation(
                payload=FitRecommendationRequest(product_id=garment_id, merchant_offer_id=offer_id),
                principal=principal_a,
                catalog_uow=uow,  # type: ignore[arg-type]
            )
        )
        assert res.status == RecommendationStatus.RECOMMENDED
        assert res.recommended_size is not None
        assert res.recommended_size.merchant_size_label == "M"
        assert res.confidence.display_to_shopper is False
        assert uow.committed is True

        # Owner retrieval works
        fetched = _run(
            get_fit_recommendation(
                recommendation_id=res.recommendation_id,  # type: ignore[arg-type]
                principal=principal_a,
                catalog_uow=uow,  # type: ignore[arg-type]
            )
        )
        assert fetched.recommendation_id == res.recommendation_id

        # Cross-shopper retrieval returns 403
        with pytest.raises(HTTPException) as exc:
            _run(
                get_fit_recommendation(
                    recommendation_id=res.recommendation_id,  # type: ignore[arg-type]
                    principal=principal_b,
                    catalog_uow=uow,  # type: ignore[arg-type]
                )
            )
        assert exc.value.status_code == 403

        # Feedback submission & retrieval by owner
        fb = _run(
            submit_fit_feedback(
                recommendation_id=res.recommendation_id,  # type: ignore[arg-type]
                payload=FitFeedbackCreateRequest(
                    reason=FitFeedbackReason.FIT_TOO_TIGHT,
                    tried_on=True,
                ),
                principal=principal_a,
                catalog_uow=uow,  # type: ignore[arg-type]
            )
        )
        assert fb.reason == FitFeedbackReason.FIT_TOO_TIGHT

        got_fb = _run(
            get_fit_feedback(
                recommendation_id=res.recommendation_id,  # type: ignore[arg-type]
                principal=principal_a,
                catalog_uow=uow,  # type: ignore[arg-type]
            )
        )
        assert got_fb.feedback_id == fb.feedback_id

        # Cross-shopper feedback access returns 403
        with pytest.raises(HTTPException) as exc2:
            _run(
                get_fit_feedback(
                    recommendation_id=res.recommendation_id,  # type: ignore[arg-type]
                    principal=principal_b,
                    catalog_uow=uow,  # type: ignore[arg-type]
                )
            )
        assert exc2.value.status_code == 403
