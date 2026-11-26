"""Tests for Repository and Service (SZ-REP-001 - SZ-REP-003, SZ-SRV-001 - SZ-SRV-003)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.catalog.size_charts.enums import (
    MeasurementBasis,
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.errors import SizeChartValidationError
from fashx.catalog.size_charts.repository import SizeChartRepository
from fashx.catalog.size_charts.schemas import (
    SizeChartRevisionCreate,
    SizeChartRow,
    SizeMeasurement,
    SizeSystemRef,
    SourceProvenance,
)
from fashx.catalog.size_charts.service import SizeChartService


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


def _make_payload(chest_m: Decimal = Decimal("98.00")) -> SizeChartRevisionCreate:
    return SizeChartRevisionCreate(
        size_system=SizeSystemRef(
            code="INTL_ALPHA",
            system_type="REGIONAL_STANDARD",
            display_name="International Alpha",
        ),
        measurement_basis=MeasurementBasis.GARMENT,
        default_unit=MeasurementUnit.CM,
        source=SourceProvenance(
            source_id="MERCHANT_FEED_V1",
            retrieved_at=datetime.now(UTC),
        ),
        rows=[
            SizeChartRow(
                merchant_size="S",
                sort_order=0,
                measurements=[
                    SizeMeasurement(
                        field_code="CHEST",
                        original_value=Decimal("92.00"),
                        original_unit=MeasurementUnit.CM,
                    )
                ],
            ),
            SizeChartRow(
                merchant_size="M",
                sort_order=1,
                measurements=[
                    SizeMeasurement(
                        field_code="CHEST",
                        original_value=chest_m,
                        original_unit=MeasurementUnit.CM,
                    )
                ],
            ),
        ],
    )


def test_repository_save_and_retrieve():
    """SZ-REP-001: Create product size chart container and persist revision."""
    repo = SizeChartRepository()
    p_id = uuid4()
    m_id = uuid4()

    async def _test():
        chart = await repo.save_chart(
            merchant_product_id=p_id,
            merchant_id=m_id,
            chart_status=SizeChartStatus.AVAILABLE,
        )
        assert chart.merchant_product_id == p_id
        assert chart.chart_status == "AVAILABLE"

        rev = await repo.save_revision(
            chart=chart,
            version=1,
            schema_version="1.0",
            size_system_code="INTL_ALPHA",
            measurement_basis="GARMENT",
            default_unit="CM",
            content_fingerprint="abc123hash",
            source_id="FEED_01",
            source_revision="1",
            source_metadata={},
            rows_data=[
                {
                    "merchant_size": "M",
                    "sort_order": 0,
                    "measurements": [
                        {
                            "field_code": "CHEST",
                            "original_value": 98.0,
                            "original_unit": "CM",
                            "normalized_value": 98.0,
                            "normalized_unit": "CM",
                        }
                    ],
                }
            ],
        )
        assert rev.version == 1
        assert rev.is_current is True

        cur = await repo.get_current_revision(chart.id)
        assert cur is not None
        assert cur.id == rev.id

    _run(_test())


def test_service_initial_ingestion():
    """SZ-SRV-001: Initial ingestion creates v1 revision."""
    service = SizeChartService()
    p_id = uuid4()
    m_id = uuid4()
    payload = _make_payload()

    async def _test():
        resp = await service.ingest_size_chart(
            merchant_product_id=p_id,
            merchant_id=m_id,
            payload=payload,
            category="TOPS",
        )
        assert resp.version == 1
        assert resp.status == SizeChartStatus.AVAILABLE
        assert resp.merchant_product_id == p_id
        assert len(resp.rows) == 2

    _run(_test())


def test_service_idempotent_ingestion_no_version_bump():
    """SZ-SRV-002: Identical ingestion creates NO_OP_UNCHANGED event without version bump."""
    service = SizeChartService()
    p_id = uuid4()
    m_id = uuid4()
    payload = _make_payload()

    async def _test():
        # First ingestion -> v1
        resp1 = await service.ingest_size_chart(
            merchant_product_id=p_id,
            merchant_id=m_id,
            payload=payload,
            category="TOPS",
        )
        assert resp1.version == 1

        # Second ingestion of identical payload -> remains v1
        resp2 = await service.ingest_size_chart(
            merchant_product_id=p_id,
            merchant_id=m_id,
            payload=payload,
            category="TOPS",
        )
        assert resp2.version == 1
        assert resp2.content_fingerprint == resp1.content_fingerprint

    _run(_test())


def test_service_updated_dimensions_increments_version():
    """SZ-SRV-003: Ingestion with changed dimensions creates v2 revision."""
    service = SizeChartService()
    p_id = uuid4()
    m_id = uuid4()
    payload1 = _make_payload(chest_m=Decimal("98.00"))
    payload2 = _make_payload(chest_m=Decimal("100.00"))

    async def _test():
        resp1 = await service.ingest_size_chart(
            merchant_product_id=p_id,
            merchant_id=m_id,
            payload=payload1,
            category="TOPS",
        )
        assert resp1.version == 1

        resp2 = await service.ingest_size_chart(
            merchant_product_id=p_id,
            merchant_id=m_id,
            payload=payload2,
            category="TOPS",
        )
        assert resp2.version == 2
        assert resp2.content_fingerprint != resp1.content_fingerprint

        # History lists both versions
        revisions = await service.list_product_revisions(p_id)
        assert len(revisions) == 2
        assert revisions[0].version == 2
        assert revisions[1].version == 1

    _run(_test())


def test_service_quarantine_on_invalid_data():
    """SZ-REP-003: Invalid chart is quarantined and raises validation error."""
    service = SizeChartService()
    p_id = uuid4()
    m_id = uuid4()
    payload = _make_payload()
    # Add category-incompatible INSEAM to TOP
    payload.rows[0].measurements.append(
        SizeMeasurement(
            field_code="INSEAM",
            original_value=Decimal("80.00"),
            original_unit=MeasurementUnit.CM,
        )
    )

    async def _test():
        with pytest.raises(SizeChartValidationError):
            await service.ingest_size_chart(
                merchant_product_id=p_id,
                merchant_id=m_id,
                payload=payload,
                category="TOPS",
            )
        assert len(service.repo._quarantine) == 1
        assert service.repo._quarantine[0].merchant_product_id == p_id

    _run(_test())
