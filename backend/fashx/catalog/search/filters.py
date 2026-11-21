from __future__ import annotations

import logging
from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog import MerchantOffer, MerchantProduct
from database.models.catalog_search import ProductSearchDocumentRecord
from database.models.catalog_taxonomy import TaxonomyCategory
from fashx.catalog.search.contracts import ProductSearchRequest

logger = logging.getLogger(__name__)


def resolve_category_descendants(session: Session, category_id: UUID) -> set[UUID]:
    """Resolve category and all its descendant category IDs in taxonomy tree."""
    target = session.get(TaxonomyCategory, category_id)
    if not target:
        return {category_id}

    descendants: set[UUID] = {target.id}
    # Query categories whose path starts with target.path
    stmt = select(TaxonomyCategory.id).where(
        TaxonomyCategory.taxonomy_version_id == target.taxonomy_version_id,
        TaxonomyCategory.path.startswith(target.path),
    )
    child_ids = set(session.scalars(stmt).all())
    descendants.update(child_ids)
    return descendants


def apply_structured_filters(
    session: Session,
    candidate_ids: Sequence[UUID],
    request: ProductSearchRequest,
) -> list[UUID]:
    """Filter candidate merchant product IDs against hard structured constraints."""
    if not candidate_ids:
        return []

    valid_ids = set(candidate_ids)

    # 1. Category Filter (with hierarchy support)
    if request.category_id is not None:
        category_scope = resolve_category_descendants(session, request.category_id)
        # Check in ProductSearchDocumentRecord or MerchantProduct
        doc_stmt = select(ProductSearchDocumentRecord.merchant_product_id).where(
            ProductSearchDocumentRecord.merchant_product_id.in_(valid_ids),
            ProductSearchDocumentRecord.category_id.in_(category_scope),
        )
        matched_cat_ids = set(session.scalars(doc_stmt).all())
        valid_ids.intersection_update(matched_cat_ids)

    # 2. Brand Filter
    if request.brand_id is not None:
        brand_stmt = select(MerchantProduct.id).where(
            MerchantProduct.id.in_(valid_ids),
            MerchantProduct.brand_id == request.brand_id,
        )
        matched_brand_ids = set(session.scalars(brand_stmt).all())
        valid_ids.intersection_update(matched_brand_ids)

    # 3. Price and Currency Filter on Active MerchantOffer
    if request.min_price is not None or request.max_price is not None:
        offer_stmt = select(
            MerchantOffer.merchant_product_id, MerchantOffer.price_minor, MerchantOffer.currency
        ).where(
            MerchantOffer.merchant_product_id.in_(valid_ids),
            MerchantOffer.status == "ACTIVE",
        )
        offers = session.execute(offer_stmt).all()
        matched_price_ids: set[UUID] = set()

        for mp_id, price_minor, curr in offers:
            # Currency check
            if request.currency and curr and curr.upper() != request.currency.upper():
                continue

            if price_minor is None:
                continue

            price_dec = Decimal(price_minor) / Decimal(100)
            passes_min = request.min_price is None or price_dec >= request.min_price
            passes_max = request.max_price is None or price_dec <= request.max_price
            if passes_min and passes_max:
                matched_price_ids.add(mp_id)

        valid_ids.intersection_update(matched_price_ids)

    # 4. Color & Occasion Filters
    if request.color_id is not None or request.occasion_id is not None:
        doc_stmt = select(ProductSearchDocumentRecord).where(
            ProductSearchDocumentRecord.merchant_product_id.in_(valid_ids)
        )
        docs = session.scalars(doc_stmt).all()
        matched_attr_ids: set[UUID] = set()

        for d in docs:
            attrs = d.indexed_attributes_json or {}
            color_match = True
            if request.color_id is not None:
                color_val = str(attrs.get("color_id", attrs.get("color", "")))
                color_match = str(request.color_id) in color_val

            occasion_match = True
            if request.occasion_id is not None:
                occ_val = str(attrs.get("occasion_id", attrs.get("occasion", "")))
                occasion_match = str(request.occasion_id) in occ_val

            if color_match and occasion_match:
                matched_attr_ids.add(d.merchant_product_id)

        valid_ids.intersection_update(matched_attr_ids)

    # Preserve candidate ordering
    return [cid for cid in candidate_ids if cid in valid_ids]


__all__ = [
    "apply_structured_filters",
    "resolve_category_descendants",
]
