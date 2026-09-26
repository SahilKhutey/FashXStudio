import pytest

from app.core.errors import ValidationError
from app.domain.promotions.enums import (
    OfferStatus,
    PromotionStatus,
)
from app.domain.promotions.lifecycle import (
    validate_offer_transition,
    validate_promotion_transition,
)


def test_promotion_activation():
    validate_promotion_transition(
        PromotionStatus.DRAFT,
        PromotionStatus.ACTIVE,
    )


def test_promotion_pause():
    validate_promotion_transition(
        PromotionStatus.ACTIVE,
        PromotionStatus.PAUSED,
    )


def test_promotion_reactivation():
    validate_promotion_transition(
        PromotionStatus.PAUSED,
        PromotionStatus.ACTIVE,
    )


def test_promotion_expire_and_archive():
    validate_promotion_transition(
        PromotionStatus.ACTIVE,
        PromotionStatus.EXPIRED,
    )
    validate_promotion_transition(
        PromotionStatus.EXPIRED,
        PromotionStatus.ARCHIVED,
    )


def test_archived_promotion_cannot_activate():
    with pytest.raises(ValidationError):
        validate_promotion_transition(
            PromotionStatus.ARCHIVED,
            PromotionStatus.ACTIVE,
        )


def test_offer_activation():
    validate_offer_transition(
        OfferStatus.DRAFT,
        OfferStatus.ACTIVE,
    )


def test_offer_pause_and_reactivation():
    validate_offer_transition(
        OfferStatus.ACTIVE,
        OfferStatus.PAUSED,
    )
    validate_offer_transition(
        OfferStatus.PAUSED,
        OfferStatus.ACTIVE,
    )


def test_archived_offer_cannot_activate():
    with pytest.raises(ValidationError):
        validate_offer_transition(
            OfferStatus.ARCHIVED,
            OfferStatus.ACTIVE,
        )
