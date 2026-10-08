from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.promotions.entities import (
    Offer,
    Promotion,
)
from fashx.domain.promotions.enums import (
    DiscountType,
    PromotionScope,
    PromotionStatus,
)


def test_promotion_validates():
    promotion = Promotion(
        name="Festival Sale",
        scope=PromotionScope.PRODUCT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20"),
    )
    promotion.validate()
    assert promotion.version == 1


def test_promotion_requires_name():
    promotion = Promotion(
        name="",
        scope=PromotionScope.PRODUCT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20"),
    )
    with pytest.raises(ValidationError):
        promotion.validate()


def test_percentage_over_100_rejected():
    promotion = Promotion(
        name="Invalid",
        scope=PromotionScope.PRODUCT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("101"),
    )
    with pytest.raises(ValidationError):
        promotion.validate()


def test_negative_discount_rejected():
    promotion = Promotion(
        name="Invalid",
        scope=PromotionScope.PRODUCT,
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("-1"),
    )
    with pytest.raises(ValidationError):
        promotion.validate()


def test_offer_requires_exactly_one_target():
    offer_zero = Offer(
        promotion_id=uuid4(),
    )
    with pytest.raises(ValidationError):
        offer_zero.validate()

    offer_two = Offer(
        promotion_id=uuid4(),
        product_id=uuid4(),
        variant_id=uuid4(),
    )
    with pytest.raises(ValidationError):
        offer_two.validate()

    offer_valid = Offer(
        promotion_id=uuid4(),
        product_id=uuid4(),
    )
    offer_valid.validate()


def test_promotion_is_effective():
    now = datetime.now(UTC)
    promotion = Promotion(
        name="Active Promo",
        status=PromotionStatus.ACTIVE,
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=1),
    )
    assert promotion.is_effective(now) is True

    # Not active status
    promotion.status = PromotionStatus.DRAFT
    assert promotion.is_effective(now) is False

    # Expired
    promotion.status = PromotionStatus.ACTIVE
    assert promotion.is_effective(now + timedelta(days=2)) is False

    # Not yet started
    assert promotion.is_effective(now - timedelta(days=2)) is False
