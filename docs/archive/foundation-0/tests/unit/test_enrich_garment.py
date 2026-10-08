import pytest
from api.app.catalog.application.enrich_garment import (
    EnrichGarmentCommand,
    EnrichGarmentUseCase,
)
from api.app.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from api.app.catalog.application.parse_size_chart import (
    ParseSizeChartCommand,
    ParseSizeChartUseCase,
)
from api.app.catalog.repositories.catalog_repository import CatalogUnitOfWork
from database.models.catalog import Merchant
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_enrich_garment_and_size_chart_use_cases(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)

    # 1. Setup Merchant and Ingest Product
    async with uow:
        merchant = Merchant(name="Uniqlo Direct", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(uow)
    ingest_cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="UQ-9812",
        title="Uniqlo Men Slim Fit Button-Down Oxford Long Sleeve Shirt Navy",
        source_url="https://uniqlo.com/shirts/9812",
        category="tops",
        subcategory="casual_shirts",
        price_minor=249000,
    )
    ingested = await ingest_uc.execute(ingest_cmd)
    garment_id = ingested.canonical_garment_id

    # 2. Enrich Garment
    enrich_uc = EnrichGarmentUseCase(uow)
    enrich_cmd = EnrichGarmentCommand(garment_id=garment_id)
    enrich_res = await enrich_uc.execute(enrich_cmd)

    assert enrich_res.garment_id == garment_id
    assert enrich_res.garment_version == 2
    assert enrich_res.attributes.get("collar") == "button_down"
    assert enrich_res.attributes.get("sleeve_length") == "long"
    assert enrich_res.attributes.get("dominant_color") == "navy"
    assert enrich_res.attributes.get("silhouette") == "slim"
    assert "collar" in enrich_res.confidence_summary

    # 3. Parse and Attach Size Chart
    size_uc = ParseSizeChartUseCase(uow)
    size_cmd = ParseSizeChartCommand(
        garment_id=garment_id,
        storage_key="charts/uniqlo_oxford.png",
        raw_rows=[
            {"size": "S", "chest": "36-38", "length": "28", "unit": "inches"},
            {"size": "M", "chest": "38-40", "length": "29", "unit": "inches"},
            {"size": "L", "chest": "40-42", "length": "30", "unit": "inches"},
        ],
        default_unit="inches",
    )
    size_res = await size_uc.execute(size_cmd)
    assert size_res.garment_id == garment_id
    assert size_res.review_status == "completed"
    assert len(size_res.measurements) == 3
    assert size_res.measurements[1]["size_label"] == "M"
    assert size_res.measurements[1]["chest_cm"] == 99.1
