from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from database.models.catalog import CanonicalGarment
from database.models.catalog_taxonomy import (
    ProductAttributeProvenanceRecord,
    ProductAttributeValueRecord,
    ProductClassificationRecord,
    TaxonomyAlias,
    TaxonomyAttribute,
    TaxonomyAttributeValueRecord,
    TaxonomyCategory,
    TaxonomyVersion,
)


@pytest.mark.asyncio
async def test_taxonomy_database_persistence_and_cascades(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Verify Phase 6.1 database models, foreign keys, and cascading deletions."""
    async with session_factory() as session:
        # 1. Create taxonomy version
        ver = TaxonomyVersion(
            version="1.0.0",
            status="ACTIVE",
            locale="en-IN",
            market="IN",
            description="FashXStudio standard taxonomy release",
        )
        session.add(ver)
        await session.flush()
        assert ver.id is not None

        # 2. Add category
        cat = TaxonomyCategory(
            taxonomy_version_id=ver.id,
            category_code="apparel_tops_t_shirts",
            parent_code="apparel_tops",
            label="T-shirts",
            path="apparel/apparel_tops/apparel_tops_t_shirts",
            level=2,
            is_leaf=True,
        )
        session.add(cat)

        # 3. Add attribute and attribute values
        attr = TaxonomyAttribute(
            taxonomy_version_id=ver.id,
            attribute_code="color",
            label="Color",
            attribute_type="enum",
            is_required=False,
            allowed_categories=["apparel_tops_t_shirts"],
        )
        session.add(attr)
        await session.flush()

        val = TaxonomyAttributeValueRecord(
            attribute_id=attr.id,
            value_code="navy",
            label="Navy Blue",
            parent_value_code="blue",
        )
        session.add(val)

        # 4. Add alias
        alias = TaxonomyAlias(
            taxonomy_version_id=ver.id,
            target_type="garment_type",
            target_code="t_shirt",
            alias_term="crewneck tee",
            source="merchant_feed",
        )
        session.add(alias)
        await session.flush()

        # 5. Create a CanonicalGarment and classify it
        garment = CanonicalGarment(
            display_name="Classic Navy Tee",
            category="apparel",
            subcategory="tops",
            gender="men",
            active=True,
            in_stock=True,
            price_minor=79900,
        )
        session.add(garment)
        await session.flush()

        classification = ProductClassificationRecord(
            garment_id=garment.id,
            taxonomy_version="1.0.0",
            category_id="apparel_tops_t_shirts",
            garment_type_id="t_shirt",
            style_family="western",
            intended_audience="men",
            occasions=["casual", "everyday"],
            classification_status="VERIFIED",
            classification_source="MERCHANT",
            classification_confidence=0.99,
        )
        session.add(classification)
        await session.flush()

        # 6. Add attribute value and provenance record
        attr_val = ProductAttributeValueRecord(
            classification_id=classification.id,
            attribute_code="color",
            value_status="KNOWN",
            value_text="navy",
            value_json={"primary": "navy", "family": "blue"},
        )
        session.add(attr_val)
        await session.flush()

        prov = ProductAttributeProvenanceRecord(
            product_attribute_value_id=attr_val.id,
            source="MERCHANT",
            source_reference="feed_sku_attr",
            confidence=1.0,
            review_status="APPROVED",
        )
        session.add(prov)
        await session.commit()

        # 7. Query back and verify persistence with eager load
        stmt = (
            select(ProductClassificationRecord)
            .where(ProductClassificationRecord.garment_id == garment.id)
            .options(
                selectinload(ProductClassificationRecord.attributes).selectinload(
                    ProductAttributeValueRecord.provenance_records
                )
            )
        )
        res = (await session.execute(stmt)).scalar_one()
        assert res.category_id == "apparel_tops_t_shirts"
        assert res.garment_type_id == "t_shirt"
        assert len(res.attributes) == 1
        assert res.attributes[0].value_text == "navy"
        assert len(res.attributes[0].provenance_records) == 1
        assert res.attributes[0].provenance_records[0].source == "MERCHANT"

        # 8. Test duplicate garment + taxonomy_version constraint
        dup_classification = ProductClassificationRecord(
            garment_id=garment.id,
            taxonomy_version="1.0.0",
            category_id="apparel_tops_t_shirts",
        )
        session.add(dup_classification)
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()
