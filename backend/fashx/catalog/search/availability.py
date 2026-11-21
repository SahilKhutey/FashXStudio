from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog import MerchantOffer, MerchantProduct
from database.models.catalog_image import CatalogImageTakedown, ImageTakedownStatus

logger = logging.getLogger(__name__)


def filter_availability_and_takedowns(
    session: Session,
    candidate_ids: Sequence[UUID],
) -> list[UUID]:
    """Strictly filter out delisted, inactive, or takedown-flagged products.

    Invariants:
    1. Takedown is a hard exclusion: any product subject to an active takedown is eliminated immediately.
    2. Delisted, discontinued, or inactive products are never returned in ordinary shopper search.
    3. Products without at least one active merchant offer are excluded.
    """
    if not candidate_ids:
        return []

    # 1. Fetch active takedown merchants/sources
    takedown_stmt = select(CatalogImageTakedown).where(
        CatalogImageTakedown.status.in_([
            ImageTakedownStatus.PROCESSING.value,
            ImageTakedownStatus.COMPLETED.value,
        ])
    )
    takedowns = session.scalars(takedown_stmt).all()
    takedown_merchants = {t.merchant_id for t in takedowns if t.merchant_id is not None}
    takedown_sources = {t.source_id for t in takedowns if t.source_id is not None}

    # 2. Query products with active status and active offers
    stmt = (
        select(MerchantProduct)
        .join(MerchantOffer, MerchantOffer.merchant_product_id == MerchantProduct.id)
        .where(
            MerchantProduct.id.in_(candidate_ids),
            MerchantProduct.status == "active",
            MerchantOffer.status == "ACTIVE",
        )
    )
    active_products = session.scalars(stmt).all()

    eligible_ids: set[UUID] = set()
    for p in active_products:
        if p.merchant_id in takedown_merchants or p.source_id in takedown_sources:
            continue
        eligible_ids.add(p.id)

    # Preserve candidate ranking order
    return [cid for cid in candidate_ids if cid in eligible_ids]


__all__ = ["filter_availability_and_takedowns"]
