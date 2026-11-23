from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from database.models.catalog_enrichment import (
    ProductAttributeEvidenceRecord,
    ProductAttributeReviewEventRecord,
    ProductAttributeReviewRecord,
    ProductEnrichmentModelRunRecord,
    ProductEnrichmentResultRecord,
    ProductEnrichmentRunRecord,
)


@pytest.mark.asyncio
async def test_enrichment_database_persistence_and_relationships(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Verify Phase 06.2 catalog enrichment database models, relationships, and queries."""
    product_uuid = uuid4()
    merchant_uuid = uuid4()

    async with session_factory() as session:
        # 1. Persist enrichment run
        run = ProductEnrichmentRunRecord(
            id=uuid4(),
            product_id=product_uuid,
            source_revision="rev-001",
            taxonomy_version="1.0.0",
            enrichment_version="1.0.0",
            status="COMPLETED",
            attempt_number=1,
            idempotency_key="hash-12345",
        )
        session.add(run)

        # 2. Persist enrichment result
        result = ProductEnrichmentResultRecord(
            id=uuid4(),
            run_id=run.id,
            product_id=product_uuid,
            taxonomy_version="1.0.0",
            enrichment_version="1.0.0",
            status="COMPLETED",
            category_id="apparel_tops_t_shirts",
            garment_type="t_shirt",
            summary_json={"color": "navy", "fit_type": "regular"},
            is_current=True,
        )
        session.add(result)

        # 3. Persist model run
        model_run = ProductEnrichmentModelRunRecord(
            id=uuid4(),
            run_id=run.id,
            provider="mock-ai",
            model_id="mock-llm",
            model_version="1.0.0",
            latency_ms=42,
            prompt_tokens=15,
            completion_tokens=5,
            cost_usd=0.0001,
        )
        session.add(model_run)

        # 4. Persist evidence record
        evidence = ProductAttributeEvidenceRecord(
            id=uuid4(),
            product_id=product_uuid,
            attribute_id="color",
            evidence_type="TITLE",
            source_record_id="sku-100",
            evidence_text="Navy Blue",
            evidence_hash="hash-evidence",
            start_offset=10,
            end_offset=19,
            extraction_method="DETERMINISTIC_TITLE_RULE",
        )
        session.add(evidence)

        # 5. Persist review record and review event
        review = ProductAttributeReviewRecord(
            id=uuid4(),
            product_id=product_uuid,
            merchant_id=merchant_uuid,
            attribute_id="occasion",
            proposed_value="festive",
            current_value=None,
            status="PENDING",
            confidence=0.74,
            flags_json=["LOW_CONFIDENCE"],
            reason="Ambiguous title context",
        )
        session.add(review)

        event = ProductAttributeReviewEventRecord(
            id=uuid4(),
            review_id=review.id,
            actor_id="user-rev-01",
            action="APPROVE",
            previous_value=None,
            new_value="festive",
            reason="Confirmed by catalog reviewer",
        )
        session.add(event)

        await session.commit()

    # Query back and verify relationships
    async with session_factory() as session:
        stmt = (
            select(ProductEnrichmentRunRecord)
            .where(ProductEnrichmentRunRecord.id == run.id)
            .options(
                selectinload(ProductEnrichmentRunRecord.results),
                selectinload(ProductEnrichmentRunRecord.model_runs),
            )
        )
        res = (await session.execute(stmt)).scalar_one()
        assert res.status == "COMPLETED"
        assert len(res.results) == 1
        assert res.results[0].category_id == "apparel_tops_t_shirts"
        assert len(res.model_runs) == 1
        assert res.model_runs[0].model_id == "mock-llm"

        # Check review and events
        review_stmt = (
            select(ProductAttributeReviewRecord)
            .where(ProductAttributeReviewRecord.id == review.id)
            .options(selectinload(ProductAttributeReviewRecord.events))
        )
        res_review = (await session.execute(review_stmt)).scalar_one()
        assert res_review.status == "PENDING"
        assert len(res_review.events) == 1
        assert res_review.events[0].action == "APPROVE"
