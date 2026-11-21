from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog import Brand, MerchantOffer, MerchantProduct
from database.models.catalog_search import (
    ProductSearchDocumentRecord,
    ProductSearchEventRecord,
    SearchSessionRecord,
)
from fashx.catalog.search.availability import filter_availability_and_takedowns
from fashx.catalog.search.candidate_merger import merge_candidates_rrf
from fashx.catalog.search.contracts import (
    ProductSearchRequest,
    ProductSearchResponse,
    ProductSearchResultItem,
    SearchBrandInfo,
    SearchPriceInfo,
    SemanticSearchRequest,
    VisualSearchRequest,
)
from fashx.catalog.search.facets import compute_facets
from fashx.catalog.search.filters import apply_structured_filters
from fashx.catalog.search.keyword_search import execute_keyword_search
from fashx.catalog.search.no_results import generate_no_result_suggestions
from fashx.catalog.search.pagination import (
    decode_cursor_token,
    generate_cursor_token,
)
from fashx.catalog.search.query_parser import parse_query
from fashx.catalog.search.ranking import apply_business_ranking
from fashx.catalog.search.semantic_search import execute_semantic_search
from fashx.catalog.search.size_filter import apply_size_and_availability_filter
from fashx.catalog.search.sorting import sort_search_results
from fashx.catalog.search.visual_search import execute_visual_search

logger = logging.getLogger(__name__)


class FashionSearchService:
    """Unified fashion search engine orchestrating multi-modal retrieval, filtering, and ranking."""

    def __init__(self, session_ttl_minutes: int = 15) -> None:
        self.session_ttl_minutes = session_ttl_minutes

    def search(
        self,
        session: Session,
        request: ProductSearchRequest,
        user_id: UUID | None = None,
    ) -> ProductSearchResponse:
        """Execute unified product search across keywords, filters, and embeddings."""
        search_id = uuid4()

        # 1. Cursor Pagination Path (Existing Search Session)
        if request.cursor:
            session_id, offset = decode_cursor_token(request.cursor)
            search_sess = session.get(SearchSessionRecord, session_id)
            if search_sess is None:
                raise ValueError("Search session not found")

            exp = search_sess.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            if exp < datetime.now(UTC):
                raise ValueError("Search session expired")

            candidate_ids = [UUID(cid) for cid in search_sess.result_ids_json]
            # Freshness / takedown re-check
            valid_ids = filter_availability_and_takedowns(session, candidate_ids)
            total = len(valid_ids)

            page_ids = valid_ids[offset : offset + request.limit]
            next_cursor = None
            if offset + request.limit < total:
                next_cursor = generate_cursor_token(session_id, offset + request.limit)

            items = self._hydrate_product_cards(session, page_ids)
            return ProductSearchResponse(
                search_id=search_id,
                query=search_sess.query_text,
                items=items,
                total=total,
                next_cursor=next_cursor,
                applied_filters=search_sess.applied_filters_json,
                sort=search_sess.sort_order,
            )

        # 2. New Search Execution
        parsed = parse_query(request.q)

        # Merge explicit filters with inferred query filters
        effective_min_p = request.min_price or parsed.inferred_min_price
        effective_max_p = request.max_price or parsed.inferred_max_price
        effective_size = request.size or parsed.inferred_size

        stream_results: dict[str, list[tuple[UUID, float]]] = {}

        # 2.1 Keyword Stream
        if parsed.clean_query:
            kw_candidates = execute_keyword_search(session, parsed.clean_query, limit=100)
            if kw_candidates:
                stream_results["keyword"] = kw_candidates

            # Also attempt semantic retrieval if text has multiple words
            if len(parsed.tokens) >= 2:
                try:
                    sem_candidates = execute_semantic_search(
                        session, parsed.clean_query, limit=100
                    )
                    if sem_candidates:
                        stream_results["semantic"] = sem_candidates
                except Exception as exc:
                    logger.debug("Semantic retrieval skipped or unavailable: %s", exc)

        # 2.2 Candidate Merger (RRF)
        if stream_results:
            merged_candidates = merge_candidates_rrf(stream_results)
            candidate_ids = [cid for cid, _ in merged_candidates]
        elif not parsed.clean_query:
            # Browse query (no keywords provided)
            mp_stmt = select(MerchantProduct.id).where(MerchantProduct.status == "active")
            candidate_ids = list(session.scalars(mp_stmt).all())
            merged_candidates = [(cid, 1.0) for cid in candidate_ids]
        else:
            # Keywords provided but no candidate matched
            candidate_ids = []
            merged_candidates = []

        # 2.3 Availability & Takedown Exclusion
        valid_ids = filter_availability_and_takedowns(session, candidate_ids)

        # 2.4 Structured Filters
        filter_req = request.model_copy(
            update={
                "min_price": effective_min_p,
                "max_price": effective_max_p,
            }
        )
        filtered_ids = apply_structured_filters(session, valid_ids, filter_req)

        # 2.5 Size & Stock Filter
        final_ids = apply_size_and_availability_filter(
            session=session,
            candidate_ids=filtered_ids,
            size=effective_size,
            in_stock_only=request.in_stock,
        )

        # 2.6 Fetch Documents & Apply Business Ranking
        score_map = dict(merged_candidates)
        ranked_candidates = [(cid, score_map.get(cid, 1.0)) for cid in final_ids]

        docs_stmt = select(ProductSearchDocumentRecord).where(
            ProductSearchDocumentRecord.merchant_product_id.in_(final_ids)
        )
        docs_map = {d.merchant_product_id: d for d in session.scalars(docs_stmt).all()}

        brand_stmt = select(Brand.id, Brand.name)
        brand_map = dict(session.execute(brand_stmt).all())

        boosted_candidates = apply_business_ranking(
            candidates=ranked_candidates,
            query_text=parsed.clean_query,
            search_docs=docs_map,
            brand_map=brand_map,
        )

        # 2.7 Hydrate Result Cards & Sort
        sorted_ids = [cid for cid, _ in boosted_candidates]
        all_items = self._hydrate_product_cards(session, sorted_ids, score_map=score_map)
        sorted_items = sort_search_results(all_items, sort_mode=request.sort)
        total = len(sorted_items)

        # 2.8 Session Creation for Stable Cursor Pagination
        session_token = f"sess_{search_id.hex}"
        search_sess = SearchSessionRecord(
            id=uuid4(),
            user_id=user_id,
            session_token=session_token,
            query_text=request.q,
            applied_filters_json={
                "category_id": str(request.category_id) if request.category_id else None,
                "brand_id": str(request.brand_id) if request.brand_id else None,
                "size": effective_size,
                "min_price": str(effective_min_p) if effective_min_p else None,
                "max_price": str(effective_max_p) if effective_max_p else None,
                "currency": request.currency,
                "in_stock": request.in_stock,
            },
            sort_order=request.sort,
            result_ids_json=[str(it.merchant_product_id) for it in sorted_items],
            total_results=total,
            expires_at=datetime.now(UTC) + timedelta(minutes=self.session_ttl_minutes),
        )
        session.add(search_sess)

        # 2.9 Pagination Slice
        page_items = sorted_items[: request.limit]
        next_cursor = None
        if request.limit < total:
            next_cursor = generate_cursor_token(search_sess.id, request.limit)

        # 2.10 No-result suggestions & Facets
        suggestions: list[str] = []
        if total == 0:
            suggestions = generate_no_result_suggestions(
                applied_filters=search_sess.applied_filters_json,
                query_text=request.q,
            )

        facets = compute_facets(session, [it.merchant_product_id for it in sorted_items])

        # 2.11 Analytics Event Logging
        event = ProductSearchEventRecord(
            session_id=search_sess.id,
            user_id=user_id,
            event_type="SEARCH_SUBMITTED",
            query=request.q,
            rank_position=None,
            metadata_json={"total": total, "sort": request.sort},
        )
        session.add(event)
        session.flush()

        return ProductSearchResponse(
            search_id=search_id,
            query=request.q,
            items=page_items,
            total=total,
            next_cursor=next_cursor,
            applied_filters=search_sess.applied_filters_json,
            suggestions=suggestions,
            facets=facets,
            sort=request.sort,
        )

    def semantic_search(
        self,
        session: Session,
        request: SemanticSearchRequest,
        user_id: UUID | None = None,
    ) -> ProductSearchResponse:
        """Execute natural-language semantic query."""
        search_req = ProductSearchRequest(
            q=request.query,
            category_id=request.filters.get("category_id"),
            max_price=request.filters.get("max_price"),
            size=request.filters.get("size"),
            currency=request.filters.get("currency", "INR"),
            limit=request.limit,
            sort="relevance",
        )
        return self.search(session, search_req, user_id=user_id)

    def visual_search(
        self,
        session: Session,
        request: VisualSearchRequest,
        user_id: UUID | None = None,
    ) -> ProductSearchResponse:
        """Execute visual similarity search."""
        candidates = execute_visual_search(
            session=session,
            query_image_asset_id=request.query_image_asset_id,
            limit=request.limit * 2,
        )
        if not candidates:
            return ProductSearchResponse(
                search_id=uuid4(),
                query="[Visual Query]",
                items=[],
                total=0,
            )

        candidate_ids = [cid for cid, _ in candidates]
        valid_ids = filter_availability_and_takedowns(session, candidate_ids)

        items = self._hydrate_product_cards(session, valid_ids[: request.limit])
        return ProductSearchResponse(
            search_id=uuid4(),
            query="[Visual Query]",
            items=items,
            total=len(items),
            sort="similarity",
        )

    def _hydrate_product_cards(
        self,
        session: Session,
        merchant_product_ids: Sequence[UUID],
        score_map: dict[UUID, float] | None = None,
    ) -> list[ProductSearchResultItem]:
        """Hydrate rich product cards joining brand, merchant, offer price, and image."""
        if not merchant_product_ids:
            return []

        scores = score_map or {}
        stmt = (
            select(MerchantProduct, Brand, MerchantOffer)
            .outerjoin(Brand, MerchantProduct.brand_id == Brand.id)
            .join(MerchantOffer, MerchantOffer.merchant_product_id == MerchantProduct.id)
            .where(
                MerchantProduct.id.in_(merchant_product_ids),
                MerchantOffer.status == "ACTIVE",
            )
        )
        rows = session.execute(stmt).all()

        item_map: dict[UUID, ProductSearchResultItem] = {}
        for mp, brand, offer in rows:
            if mp.id in item_map:
                continue

            brand_name = brand.name if brand else "Unbranded"
            brand_id = brand.id if brand else None

            # Primary image URL or fallback
            img_url = mp.source_url if hasattr(mp, "source_url") else None

            item = ProductSearchResultItem(
                product_id=mp.canonical_garment_id or mp.id,
                merchant_product_id=mp.id,
                title=mp.title,
                brand=SearchBrandInfo(id=brand_id, name=brand_name),
                price=SearchPriceInfo(
                    amount=(
                        Decimal(offer.price_minor) / Decimal(100)
                        if offer.price_minor is not None
                        else Decimal("0.00")
                    ),
                    currency=offer.currency or "INR",
                ),
                availability=mp.availability or "IN_STOCK",
                matched_attributes=list(mp.title.split()[:3]),
                primary_image_url=img_url,
                similarity_score=scores.get(mp.id),
            )
            item_map[mp.id] = item

        # Return in requested ID order
        return [item_map[mp_id] for mp_id in merchant_product_ids if mp_id in item_map]


__all__ = ["FashionSearchService"]
