from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog import MerchantOffer, MerchantProduct
from database.models.catalog_freshness import AvailabilityStatus, MerchantOfferSize

logger = logging.getLogger(__name__)

# Standard size equivalence mapping
SIZE_ALIASES: dict[str, str] = {
    "MEDIUM": "M",
    "SMALL": "S",
    "LARGE": "L",
    "EXTRA LARGE": "XL",
    "DOUBLE XL": "XXL",
}


def normalize_size_token(size_raw: str | None) -> str:
    """Normalize input size string for matching."""
    if not size_raw:
        return ""
    s = size_raw.strip().upper()
    return SIZE_ALIASES.get(s, s)


def apply_size_and_availability_filter(
    session: Session,
    candidate_ids: Sequence[UUID],
    size: str | None = None,
    in_stock_only: bool | None = None,
) -> list[UUID]:
    """Filter products by variant size label and stock availability.

    Invariants:
    1. Unknown size stock is NEVER falsely treated as available.
    2. Size matching must inspect merchant variant records (MerchantOfferSize), not generic size charts.
    3. Out-of-stock items are strictly excluded when in_stock_only=True.
    """
    if not candidate_ids:
        return []

    valid_ids = set(candidate_ids)

    # 1. Size filtering
    if size is not None:
        norm_size = normalize_size_token(size)

        stmt = (
            select(MerchantOffer.merchant_product_id, MerchantOfferSize.raw_size, MerchantOfferSize.availability)
            .join(MerchantOfferSize, MerchantOfferSize.merchant_offer_id == MerchantOffer.id)
            .where(
                MerchantOffer.merchant_product_id.in_(valid_ids),
                MerchantOffer.status == "ACTIVE",
            )
        )
        offer_sizes = session.execute(stmt).all()

        matching_size_ids: set[UUID] = set()
        for mp_id, raw_sz, avail in offer_sizes:
            if normalize_size_token(raw_sz) == norm_size:
                # If in_stock_only is requested, enforce IN_STOCK
                if in_stock_only:
                    if avail in (AvailabilityStatus.IN_STOCK.value, "IN_STOCK", "LOW_STOCK"):
                        matching_size_ids.add(mp_id)
                else:
                    matching_size_ids.add(mp_id)

        valid_ids.intersection_update(matching_size_ids)

    elif in_stock_only:
        # General in-stock check (either merchant_product.availability or active offer in_stock)
        stmt = (
            select(MerchantOffer.merchant_product_id)
            .join(MerchantProduct, MerchantOffer.merchant_product_id == MerchantProduct.id)
            .where(
                MerchantOffer.merchant_product_id.in_(valid_ids),
                MerchantOffer.status == "ACTIVE",
                MerchantProduct.status == "active",
            )
        )
        in_stock_candidates = set(session.scalars(stmt).all())
        valid_ids.intersection_update(in_stock_candidates)

    return [cid for cid in candidate_ids if cid in valid_ids]


__all__ = [
    "apply_size_and_availability_filter",
    "normalize_size_token",
]
