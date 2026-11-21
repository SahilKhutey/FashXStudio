from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog import Brand, MerchantOffer, MerchantProduct
from database.models.catalog_search import ProductSearchDocumentRecord


def compute_facets(
    session: Session,
    matching_product_ids: Sequence[UUID],
) -> dict[str, list[dict[str, Any]]]:
    """Compute facet counts (brands, categories, price range) for current search results."""
    if not matching_product_ids:
        return {"brands": [], "categories": [], "price_range": []}

    # 1. Brands
    stmt = (
        select(Brand.id, Brand.name)
        .join(MerchantProduct, MerchantProduct.brand_id == Brand.id)
        .where(MerchantProduct.id.in_(matching_product_ids))
    )
    brand_rows = session.execute(stmt).all()
    brand_counter = Counter(brand_rows)
    brands_facet = [
        {"id": str(bid), "name": name, "count": cnt}
        for (bid, name), cnt in brand_counter.most_common(10)
    ]

    # 2. Categories & Attributes from search documents
    doc_stmt = select(ProductSearchDocumentRecord).where(
        ProductSearchDocumentRecord.merchant_product_id.in_(matching_product_ids)
    )
    docs = session.scalars(doc_stmt).all()
    category_counter: Counter[str] = Counter()
    for d in docs:
        if d.category_id:
            category_counter[str(d.category_id)] += 1

    categories_facet = [
        {"id": cid, "count": cnt} for cid, cnt in category_counter.most_common(10)
    ]

    # 3. Price Range from Offers
    price_stmt = select(MerchantOffer.price_minor).where(
        MerchantOffer.merchant_product_id.in_(matching_product_ids),
        MerchantOffer.status == "ACTIVE",
    )
    prices = session.scalars(price_stmt).all()
    price_facet: list[dict[str, Any]] = []
    if prices:
        dec_prices = [Decimal(p) / Decimal(100) for p in prices if p is not None]
        if dec_prices:
            price_facet = [{
                "min_price": str(min(dec_prices)),
                "max_price": str(max(dec_prices)),
            }]

    return {
        "brands": brands_facet,
        "categories": categories_facet,
        "price_range": price_facet,
    }


__all__ = ["compute_facets"]
