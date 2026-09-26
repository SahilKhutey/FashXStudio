from __future__ import annotations

from app.core.errors import ValidationError

from .enums import (
    OfferStatus,
    PromotionStatus,
)

_PROMOTION_TRANSITIONS = {
    PromotionStatus.DRAFT: {
        PromotionStatus.ACTIVE,
        PromotionStatus.ARCHIVED,
    },
    PromotionStatus.ACTIVE: {
        PromotionStatus.PAUSED,
        PromotionStatus.EXPIRED,
        PromotionStatus.ARCHIVED,
    },
    PromotionStatus.PAUSED: {
        PromotionStatus.ACTIVE,
        PromotionStatus.EXPIRED,
        PromotionStatus.ARCHIVED,
    },
    PromotionStatus.EXPIRED: {
        PromotionStatus.ARCHIVED,
    },
    PromotionStatus.ARCHIVED: set(),
}


_OFFER_TRANSITIONS = {
    OfferStatus.DRAFT: {
        OfferStatus.ACTIVE,
        OfferStatus.ARCHIVED,
    },
    OfferStatus.ACTIVE: {
        OfferStatus.PAUSED,
        OfferStatus.EXPIRED,
        OfferStatus.ARCHIVED,
    },
    OfferStatus.PAUSED: {
        OfferStatus.ACTIVE,
        OfferStatus.EXPIRED,
        OfferStatus.ARCHIVED,
    },
    OfferStatus.EXPIRED: {
        OfferStatus.ARCHIVED,
    },
    OfferStatus.ARCHIVED: set(),
}


def validate_promotion_transition(
    current: PromotionStatus,
    target: PromotionStatus,
) -> None:
    if target not in _PROMOTION_TRANSITIONS[current]:
        raise ValidationError(
            "Invalid promotion status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )


def validate_offer_transition(
    current: OfferStatus,
    target: OfferStatus,
) -> None:
    if target not in _OFFER_TRANSITIONS[current]:
        raise ValidationError(
            "Invalid offer status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )
