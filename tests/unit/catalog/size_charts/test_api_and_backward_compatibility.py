"""Tests for API and Backward Compatibility (SZ-API-001 - SZ-API-005, SZ-E2E-001)."""

from __future__ import annotations

import inspect
from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.catalog.size_charts.enums import (
    MeasurementBasis,
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.schemas import (
    MerchantSizeChartResponse,
    SizeChartRow,
    SizeChartUnavailableResponse,
)
from fashx.catalog.size_charts.service import SizeChartService, SizeChartValidationError


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
    # 30 inches to cm = 76.20 cm
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

    # Missing basis
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

    # Empty size row
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
