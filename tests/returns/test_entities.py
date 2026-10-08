from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.returns.entities import (
    CancellationRequest,
    Refund,
    ReplacementRequest,
    ReturnLine,
    ReturnRequest,
)
from fashx.domain.returns.enums import (
    CancellationStatus,
    RefundReason,
    RefundStatus,
    ReplacementStatus,
    ReturnReason,
    ReturnStatus,
)


def test_return_requires_order():
    request = ReturnRequest(customer_id=uuid4())
    with pytest.raises(ValidationError, match="Return requires order ID"):
        request.validate()


def test_return_requires_customer():
    request = ReturnRequest(order_id=uuid4())
    with pytest.raises(ValidationError, match="Return requires customer ID"):
        request.validate()


def test_valid_return():
    request = ReturnRequest(
        order_id=uuid4(),
        customer_id=uuid4(),
        reason=ReturnReason.SIZE_ISSUE,
        notes="Too small",
    )
    request.validate()
    assert request.status == ReturnStatus.REQUESTED
    assert request.version == 1

    orig_updated = request.updated_at
    request.touch()
    assert request.version == 2
    assert request.updated_at >= orig_updated


def test_return_version_invalid():
    request = ReturnRequest(
        order_id=uuid4(),
        customer_id=uuid4(),
        version=0,
    )
    with pytest.raises(ValidationError, match="Return version must be positive"):
        request.validate()


def test_return_line_quantity():
    line = ReturnLine(
        return_id=uuid4(),
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=0,
    )
    with pytest.raises(ValidationError, match="Return quantity must be at least 1"):
        line.validate()


def test_return_line_negative_refund():
    line = ReturnLine(
        return_id=uuid4(),
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
        refund_amount=Decimal("-1.00"),
    )
    with pytest.raises(ValidationError, match="Refund amount cannot be negative"):
        line.validate()


def test_return_line_missing_ids():
    ret_id = uuid4()
    ol_id = uuid4()
    p_id = uuid4()

    with pytest.raises(ValidationError, match="Return line requires return ID"):
        ReturnLine(order_line_id=ol_id, product_id=p_id).validate()

    with pytest.raises(ValidationError, match="Return line requires order line ID"):
        ReturnLine(return_id=ret_id, product_id=p_id).validate()

    with pytest.raises(ValidationError, match="Return line requires product ID"):
        ReturnLine(return_id=ret_id, order_line_id=ol_id).validate()

    valid_line = ReturnLine(
        return_id=ret_id,
        order_line_id=ol_id,
        product_id=p_id,
        quantity=2,
        refund_amount=Decimal("1500.00"),
    )
    valid_line.validate()


def test_cancellation_validation():
    with pytest.raises(ValidationError, match="Cancellation requires order ID"):
        CancellationRequest(customer_id=uuid4(), reason="Changed mind").validate()

    with pytest.raises(ValidationError, match="Cancellation requires customer ID"):
        CancellationRequest(order_id=uuid4(), reason="Changed mind").validate()

    with pytest.raises(ValidationError, match="Cancellation reason is required"):
        CancellationRequest(order_id=uuid4(), customer_id=uuid4(), reason="   ").validate()

    cancellation = CancellationRequest(
        order_id=uuid4(),
        customer_id=uuid4(),
        reason="Found better price",
    )
    cancellation.validate()
    assert cancellation.status == CancellationStatus.REQUESTED
    cancellation.touch()
    assert cancellation.version == 2


def test_refund_amount_positive():
    refund = Refund(
        order_id=uuid4(),
        amount=Decimal("0"),
    )
    with pytest.raises(ValidationError, match="Refund amount must be positive"):
        refund.validate()

    refund_neg = Refund(
        order_id=uuid4(),
        amount=Decimal("-10.00"),
    )
    with pytest.raises(ValidationError, match="Refund amount must be positive"):
        refund_neg.validate()


def test_refund_currency_and_order():
    with pytest.raises(ValidationError, match="Refund requires order ID"):
        Refund(amount=Decimal("100.00")).validate()

    with pytest.raises(ValidationError, match="Currency must be a 3-character code"):
        Refund(order_id=uuid4(), amount=Decimal("100.00"), currency="US").validate()

    valid_refund = Refund(
        order_id=uuid4(),
        amount=Decimal("499.99"),
        currency="INR",
        reason=RefundReason.ORDER_CANCELLED,
    )
    valid_refund.validate()
    assert valid_refund.status == RefundStatus.REQUESTED
    valid_refund.touch()
    assert valid_refund.version == 2


def test_replacement_validation():
    with pytest.raises(ValidationError, match="Replacement requires order ID"):
        ReplacementRequest(
            original_order_line_id=uuid4(),
            replacement_product_id=uuid4(),
        ).validate()

    with pytest.raises(ValidationError, match="Replacement requires original order line"):
        ReplacementRequest(
            order_id=uuid4(),
            replacement_product_id=uuid4(),
        ).validate()

    with pytest.raises(ValidationError, match="Replacement product is required"):
        ReplacementRequest(
            order_id=uuid4(),
            original_order_line_id=uuid4(),
        ).validate()

    replacement = ReplacementRequest(
        order_id=uuid4(),
        original_order_line_id=uuid4(),
        replacement_product_id=uuid4(),
        replacement_variant_id=uuid4(),
    )
    replacement.validate()
    assert replacement.status == ReplacementStatus.REQUESTED
    replacement.touch()
    assert replacement.version == 2
