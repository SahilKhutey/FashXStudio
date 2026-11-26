"""Tests for API and Backward Compatibility (SZ-API-001 - SZ-API-005, SZ-E2E-001)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from fashx.catalog.size_charts.enums import (
    AvailabilityStatus,
    MeasurementBasis,
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.repository import SizeChartRepository
from fashx.catalog.size_charts.router import (
    get_product_size_chart,
    get_product_variant_availability,
    ingest_product_size_chart,
    list_registered_size_systems,
    list_size_chart_revisions,
)
from fashx.catalog.size_charts.schemas import (
    MerchantSizeChartResponse,
    SizeChartRevisionCreate,
    SizeChartRow,
    SizeChartUnavailableResponse,
    SizeMeasurement,
    SizeSystemRef,
    SourceProvenance,
)
from fashx.catalog.size_charts.service import SizeChartService, SizeChartValidationError
from fashx.main import app
from fashx.security.deps import Principal, get_principal, require_role
from fashx.security.errors import ApiError


def _run(coro):
    """Run an async coroutine synchronously using generator stepping to avoid Windows IOCP deadlocks."""
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
    return val


def test_backward_compatibility_convert_to_cm():
    """Verify convert_to_cm retains exact Phase 07.8 behaviour."""
    val_cm = SizeChartService.convert_to_cm(Decimal("30.0"), MeasurementUnit.INCH)
    assert val_cm == Decimal("76.20")

    val_cm_str = SizeChartService.convert_to_cm(Decimal("100.0"), "CM")
    assert val_cm_str == Decimal("100.00")


def test_backward_compatibility_validate_and_normalize_chart():
    """SZ-E2E-001: validate_and_normalize_chart preserves Phase 07.8 behavior."""
    service = SizeChartService()
    p_id = str(uuid4())
    m_id = str(uuid4())

    rows = [
        SizeChartRow(
            merchant_size="M",
            chest=Decimal("98.00"),
            waist=Decimal("84.00"),
            hip=Decimal("102.00"),
            length=Decimal("72.00"),
            shoulder=Decimal("46.00"),
        )
    ]

    resp = service.validate_and_normalize_chart(
        merchant_id=m_id,
        merchant_product_id=p_id,
        merchant_name="Acme Fashion",
        basis=MeasurementBasis.GARMENT,
        unit=MeasurementUnit.CM,
        source_reference="FEED_REF_01",
        source_revision="rev_1",
        rows=rows,
    )

    assert isinstance(resp, MerchantSizeChartResponse)
    assert resp.merchant_product_id == p_id
    assert resp.merchant_name == "Acme Fashion"
    assert resp.status == SizeChartStatus.VERIFIED
    assert resp.is_stale is False
    assert len(resp.rows) == 1
    assert resp.rows[0].chest == Decimal("98.00")


def test_backward_compatibility_validation_errors():
    """Verify validation error invariants in validate_and_normalize_chart."""
    service = SizeChartService()
    p_id = str(uuid4())
    m_id = str(uuid4())

    with pytest.raises(SizeChartValidationError, match="Invalid or missing measurement basis"):
        service.validate_and_normalize_chart(
            merchant_id=m_id,
            merchant_product_id=p_id,
            merchant_name="Acme",
            basis="INVALID_BASIS",
            unit=MeasurementUnit.CM,
            source_reference="REF",
            source_revision="1",
            rows=[{"merchant_size": "M", "chest": 98}],
        )

    with pytest.raises(SizeChartValidationError, match="cannot be empty"):
        service.validate_and_normalize_chart(
            merchant_id=m_id,
            merchant_product_id=p_id,
            merchant_name="Acme",
            basis=MeasurementBasis.GARMENT,
            unit=MeasurementUnit.CM,
            source_reference="REF",
            source_revision="1",
            rows=[{"merchant_size": "", "chest": 98}],
        )


def test_backward_compatibility_get_unavailable_response():
    """Verify get_unavailable_response returns explicit unavailable state."""
    service = SizeChartService()
    p_id = str(uuid4())
    resp = service.get_unavailable_response(p_id)
    assert isinstance(resp, SizeChartUnavailableResponse)
    assert resp.product_id == p_id
    assert resp.status == "UNAVAILABLE"


class _FakeCatalogUOW:
    """In-memory UOW stub for FastAPI route unit testing."""

    def __init__(
        self,
        products: dict[UUID, object],
        garments: dict[UUID, object] | None = None,
        offers: dict[UUID, list[object]] | None = None,
    ):
        self._products = products
        self._garments = garments or {}
        self._offers = offers or {}
        self.committed = False
        self.session = self
        self.canonical_garments = SimpleNamespace(get_by_id=self._get_garment)
        self.offers = SimpleNamespace(list_for_garment=self._list_offers)

    async def _get_garment(self, gid: UUID):
        return self._garments.get(gid)

    async def _list_offers(self, gid: UUID):
        return self._offers.get(gid, [])

    async def get(self, model_cls, obj_id: UUID):
        return self._products.get(obj_id)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def test_api_routes_mounted_with_auth_in_main_app():
    """Verify all size chart routes are mounted in app with default-deny auth and RBAC."""
    spec_paths = app.openapi()["paths"]
    expected_routes = [
        ("/api/v1/products/{product_id}/size-chart", "get"),
        ("/api/v1/products/{product_id}/size-chart", "post"),
        ("/api/v1/products/{product_id}/size-chart/revisions", "get"),
        ("/api/v1/products/{product_id}/variants", "get"),
        ("/api/v1/products/{product_id}/availability", "get"),
        ("/api/v1/size-systems", "get"),
    ]
    for path, method in expected_routes:
        assert path in spec_paths, f"Missing path {path} in FastAPI OpenAPI schema"
        assert method in spec_paths[path], f"Missing method {method} on {path}"

    # Verify included routers enforce get_principal on every mounted size-chart router
    mounted = [
        r
        for r in app.routes
        if hasattr(r, "original_router")
        and getattr(getattr(r, "original_router", None), "prefix", None)
        in ("/products", "/size-systems")
        and any("size" in tag for tag in getattr(r.original_router, "tags", []))
    ]
    assert len(mounted) == 2
    for included in mounted:
        deps = {
            getattr(d, "dependency", None)
            for d in getattr(included.include_context, "dependencies", ())
        }
        assert get_principal in deps, f"Router {included.original_router.prefix} missing get_principal"

    # Verify require_role("admin") blocks non-admin on POST
    admin_checker = require_role("admin")
    shopper = Principal(user_id="shopper-1", subject="shopper-1", roles=frozenset({"shopper"}))
    with pytest.raises(ApiError) as exc_info:
        _run(admin_checker(shopper))
    assert exc_info.value.status == 403


def test_api_size_systems_deduplicated():
    """GET /api/v1/size-systems returns deduplicated registered sizing systems."""
    items = _run(list_registered_size_systems())
    codes = [item.code for item in items]
    assert len(codes) == len(set(codes))
    assert "INTL_ALPHA" in codes
    assert "ETHNIC_INDIA" in codes


def test_api_get_size_chart_404_and_unavailable():
    """SZ-API-002 / SZ-API-003: Missing product -> 404; product without chart -> UNAVAILABLE."""
    prod_id = uuid4()
    merchant_id = uuid4()
    missing_id = uuid4()
    fake_uow = _FakeCatalogUOW(
        products={prod_id: SimpleNamespace(id=prod_id, merchant_id=merchant_id)}
    )
    in_mem_repo = SizeChartRepository(session=None)

    with patch(
        "fashx.catalog.size_charts.router.SizeChartService",
        lambda session=None: SizeChartService(session_or_db=None, repository=in_mem_repo),
    ):
        with pytest.raises(HTTPException) as exc_missing:
            _run(get_product_size_chart(missing_id, unit=None, system=None, catalog_uow=fake_uow))
        assert exc_missing.value.status_code == 404

        unavail = _run(
            get_product_size_chart(prod_id, unit=None, system=None, catalog_uow=fake_uow)
        )
        assert isinstance(unavail, SizeChartUnavailableResponse)
        assert unavail.status == "UNAVAILABLE"
        assert unavail.product_id == str(prod_id)


def test_api_ingest_and_retrieve_size_chart_and_garment_resolution():
    """SZ-API-001 / SZ-API-004 / SZ-API-005: Ingestion, retrieval, canonical resolution, and 422 quarantine."""
    prod_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    other_merchant_id = uuid4()
    fake_uow = _FakeCatalogUOW(
        products={prod_id: SimpleNamespace(id=prod_id, merchant_id=merchant_id)},
        garments={garment_id: SimpleNamespace(id=garment_id, active=True)},
        offers={
            garment_id: [
                SimpleNamespace(
                    status="ACTIVE",
                    takedown_status="NONE",
                    merchant_product_id=prod_id,
                )
            ]
        },
    )
    in_mem_repo = SizeChartRepository(session=None)

    payload = SizeChartRevisionCreate(
        size_system=SizeSystemRef(code="INTL_ALPHA", display_name="International Alpha"),
        measurement_basis=MeasurementBasis.GARMENT,
        default_unit=MeasurementUnit.CM,
        source=SourceProvenance(source_id="MERCHANT_API", retrieved_at=datetime.now(UTC)),
        rows=[
            SizeChartRow(
                merchant_size="M",
                sort_order=0,
                measurements=[
                    SizeMeasurement(
                        field_code="CHEST",
                        original_value=Decimal("98.00"),
                        original_unit=MeasurementUnit.CM,
                    )
                ],
            )
        ],
    )

    with patch(
        "fashx.catalog.size_charts.router.SizeChartService",
        lambda session=None: SizeChartService(session_or_db=None, repository=in_mem_repo),
    ):
        # 1. Wrong merchant owner -> 403
        with pytest.raises(HTTPException) as exc_owner:
            _run(
                ingest_product_size_chart(
                    prod_id,
                    payload=payload,
                    merchant_id=other_merchant_id,
                    category="TOPS",
                    catalog_uow=fake_uow,
                )
            )
        assert exc_owner.value.status_code == 403

        # 2. Valid ingestion -> commits & returns v1 chart
        created = _run(
            ingest_product_size_chart(
                prod_id,
                payload=payload,
                merchant_id=merchant_id,
                category="TOPS",
                catalog_uow=fake_uow,
            )
        )
        assert created.version == 1
        assert created.rows[0].merchant_size == "M"
        assert fake_uow.committed is True

        # 3. Retrieve by MerchantProduct.id in INCH AND by CanonicalGarment.id
        fetched_inch = _run(
            get_product_size_chart(
                prod_id, unit=MeasurementUnit.INCH, system=None, catalog_uow=fake_uow
            )
        )
        assert fetched_inch.display_unit == MeasurementUnit.INCH

        fetched_via_garment = _run(
            get_product_size_chart(garment_id, unit=None, system=None, catalog_uow=fake_uow)
        )
        assert fetched_via_garment.merchant_product_id == prod_id

        revs = _run(list_size_chart_revisions(prod_id, catalog_uow=fake_uow))
        assert len(revs) == 1

        avail = _run(get_product_variant_availability(prod_id, catalog_uow=fake_uow))
        assert avail.overall_status == AvailabilityStatus.UNKNOWN

        # 4. Invalid category field -> 422 & quarantine persisted
        bad_payload = SizeChartRevisionCreate(
            size_system=SizeSystemRef(code="INTL_ALPHA", display_name="International Alpha"),
            measurement_basis=MeasurementBasis.GARMENT,
            default_unit=MeasurementUnit.CM,
            source=SourceProvenance(source_id="MERCHANT_API", retrieved_at=datetime.now(UTC)),
            rows=[
                SizeChartRow(
                    merchant_size="M",
                    measurements=[
                        SizeMeasurement(
                            field_code="INSEAM",
                            original_value=Decimal("80.00"),
                            original_unit=MeasurementUnit.CM,
                        )
                    ],
                )
            ],
        )
        with pytest.raises(HTTPException) as exc_invalid:
            _run(
                ingest_product_size_chart(
                    prod_id,
                    payload=bad_payload,
                    merchant_id=merchant_id,
                    category="TOPS",
                    catalog_uow=fake_uow,
                )
            )
        assert exc_invalid.value.status_code == 422
        assert len(in_mem_repo._quarantine) == 1
