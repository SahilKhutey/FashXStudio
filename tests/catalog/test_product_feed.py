from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, CatalogSource, IngestRun, Merchant
from fashx.catalog.acquisition.product_feed import (
    normalize_product,
    read_csv_rows,
)
from fashx.catalog.acquisition.sync_service import CatalogSyncService
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import ValidationError


def valid_row() -> dict[str, str]:
    return {
        "source_product_id": "partner-tee-001",
        "title": "Classic Cotton T-Shirt",
        "source_url": "https://partner.example/products/tee-001",
        "category": "tops",
        "price_minor": "79900",
        "currency": "INR",
        "in_stock": "true",
        "sizes_in_stock": "S|M|L|XL",
        "subcategory": "t-shirt",
        "description": "Cotton crew-neck shirt",
        "brand_id": "",
        "item_group_id": "tee-group-001",
    }


# ---------------------------------------------------------------------------
# Unit Tests (Normalization & Validation)
# ---------------------------------------------------------------------------


def test_normalizes_valid_product() -> None:
    product = normalize_product(valid_row())
    assert product.source_product_id == "partner-tee-001"
    assert product.title == "Classic Cotton T-Shirt"
    assert product.category == "tops"
    assert product.price_minor == 79900
    assert product.currency == "INR"
    assert product.in_stock is True
    assert product.sizes_in_stock == ("S", "M", "L", "XL")
    assert product.subcategory == "t-shirt"
    assert product.description == "Cotton crew-neck shirt"
    assert product.brand_id is None
    assert product.item_group_id == "tee-group-001"
    assert len(product.content_hash) == 64


def test_hash_is_stable_for_identical_records() -> None:
    row = valid_row()
    assert normalize_product(row).content_hash == normalize_product(row).content_hash


def test_hash_changes_when_price_changes() -> None:
    row1 = valid_row()
    row2 = dict(valid_row(), price_minor="89900")
    assert normalize_product(row1).content_hash != normalize_product(row2).content_hash


def test_normalizes_brand_id_as_uuid() -> None:
    bid = uuid4()
    row = dict(valid_row(), brand_id=str(bid))
    product = normalize_product(row)
    assert isinstance(product.brand_id, UUID)
    assert product.brand_id == bid


def test_rejects_missing_source_product_id() -> None:
    row = dict(valid_row(), source_product_id="")
    with pytest.raises(ValidationError) as exc:
        normalize_product(row)
    assert exc.value.field == "source_product_id"


def test_rejects_missing_title() -> None:
    row = dict(valid_row(), title="")
    with pytest.raises(ValidationError) as exc:
        normalize_product(row)
    assert exc.value.field == "title"


def test_rejects_missing_or_invalid_source_url() -> None:
    row_empty = dict(valid_row(), source_url="")
    with pytest.raises(ValidationError) as exc1:
        normalize_product(row_empty)
    assert exc1.value.field == "source_url"

    row_scheme = dict(valid_row(), source_url="ftp://invalid.com/file")
    with pytest.raises(ValidationError) as exc2:
        normalize_product(row_scheme)
    assert exc2.value.field == "source_url"

    row_relative = dict(valid_row(), source_url="/products/item-1")
    with pytest.raises(ValidationError) as exc3:
        normalize_product(row_relative)
    assert exc3.value.field == "source_url"


def test_rejects_unapproved_category() -> None:
    row = dict(valid_row(), category="footwear")
    with pytest.raises(ValidationError) as exc:
        normalize_product(row)
    assert exc.value.field == "category"


def test_rejects_negative_price() -> None:
    row = dict(valid_row(), price_minor="-100")
    with pytest.raises(ValidationError) as exc:
        normalize_product(row)
    assert exc.value.field == "price_minor"


def test_read_csv_rows_missing_required_columns(tmp_path: Path) -> None:
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("source_product_id,title\n1,Shirt\n", encoding="utf-8")
    with pytest.raises(ValidationError) as exc:
        list(read_csv_rows(csv_file))
    assert exc.value.field == "csv_headers"


def test_read_csv_rows_success(tmp_path: Path) -> None:
    csv_file = tmp_path / "good.csv"
    csv_file.write_text(
        "source_product_id,title,source_url,category,price_minor\n"
        "P1,Top 1,https://example.com/p1,tops,1000\n"
        "P2,Bottom 2,https://example.com/p2,bottoms,2000\n",
        encoding="utf-8",
    )
    rows = list(read_csv_rows(csv_file))
    assert len(rows) == 2
    assert rows[0][0] == 2
    assert rows[0][1]["source_product_id"] == "P1"
    assert rows[1][0] == 3
    assert rows[1][1]["source_product_id"] == "P2"


# ---------------------------------------------------------------------------
# Integration Tests (CSV Sync Service & Idempotency)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_import_csv_feed_success_and_idempotent_sync(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Importing a CSV feed must create products, and re-importing must update prices idempotently."""
    uow = CatalogUnitOfWork(session_factory)

    # 1. Register merchant and cleared source
    async with uow:
        merchant = Merchant(name="Partner Retailer", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="feed_url",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="hotlink",
        )
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    # 2. Write CSV feed
    csv_file = tmp_path / "feed.csv"
    csv_file.write_text(
        "source_product_id,title,source_url,category,price_minor,currency,in_stock,sizes_in_stock\n"
        "SKU-FEED-01,Oxford Shirt,https://partner.example/sku-01,tops,199900,INR,true,S|M|L\n"
        "SKU-FEED-02,Chino Pants,https://partner.example/sku-02,bottoms,249900,INR,true,30|32\n",
        encoding="utf-8",
    )

    sync_service = CatalogSyncService(session_factory)
    report1 = await sync_service.import_csv_feed(csv_file, source_id, merchant_id)

    assert report1.total_rows == 2
    assert report1.imported == 2
    assert report1.failed == 0

    # Verify canonical garments in database
    async with uow:
        garments = (await uow.session.scalars(select(CanonicalGarment))).all()
        assert len(garments) == 2
        garment_map = {g.display_name: g for g in garments}
        assert "Oxford Shirt" in garment_map
        assert garment_map["Oxford Shirt"].price_minor == 199900
        garment1_id = garment_map["Oxford Shirt"].id

        # Ingestion run history must be persisted
        runs = (await uow.session.scalars(select(IngestRun))).all()
        assert len(runs) >= 1
        assert runs[-1].status == "ok"
        assert runs[-1].counts["imported"] == 2

    # 3. Second import with price update (Idempotency test)
    csv_file_v2 = tmp_path / "feed_v2.csv"
    csv_file_v2.write_text(
        "source_product_id,title,source_url,category,price_minor,currency,in_stock,sizes_in_stock\n"
        "SKU-FEED-01,Oxford Shirt Updated,https://partner.example/sku-01,tops,179900,INR,true,S|M|L\n"
        "SKU-FEED-02,Chino Pants,https://partner.example/sku-02,bottoms,249900,INR,false,30|32\n",
        encoding="utf-8",
    )
    report2 = await sync_service.import_csv_feed(csv_file_v2, source_id, merchant_id)
    assert report2.imported == 2
    assert report2.failed == 0

    async with uow:
        garments_v2 = (await uow.session.scalars(select(CanonicalGarment))).all()
        # Garment count must remain 2 (no duplicates created!)
        assert len(garments_v2) == 2
        garment_v2_map = {g.display_name: g for g in garments_v2}
        assert "Oxford Shirt Updated" in garment_v2_map
        assert garment_v2_map["Oxford Shirt Updated"].id == garment1_id
        assert garment_v2_map["Oxford Shirt Updated"].price_minor == 179900


@pytest.mark.asyncio
async def test_import_csv_feed_skips_invalid_rows_without_aborting_batch(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Invalid rows must be captured in report without terminating import of valid rows."""
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Tolerant Retailer", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="feed_url",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="hotlink",
        )
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    # 1 valid row, 1 row with bad category, 1 row with negative price
    csv_file = tmp_path / "mixed.csv"
    csv_file.write_text(
        "source_product_id,title,source_url,category,price_minor\n"
        "SKU-VALID,Valid Blouse,https://partner.example/sku-v,tops,150000\n"
        "SKU-INVALID-CAT,Sneakers,https://partner.example/sku-bad,shoes,200000\n"
        "SKU-INVALID-PRICE,Bad Price,https://partner.example/sku-neg,tops,-500\n",
        encoding="utf-8",
    )

    sync_service = CatalogSyncService(session_factory)
    report = await sync_service.import_csv_feed(csv_file, source_id, merchant_id)

    assert report.total_rows == 3
    assert report.imported == 1
    assert report.failed == 2
    assert len(report.errors) == 2

    async with uow:
        garments = (await uow.session.scalars(select(CanonicalGarment))).all()
        assert len(garments) == 1
        assert garments[0].display_name == "Valid Blouse"


@pytest.mark.asyncio
async def test_import_csv_feed_unapproved_source_fails_preflight(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Preflight check must refuse import if source status is pending or display rights are disabled."""
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Pending Retailer", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="feed_url",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="hotlink",
        )
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    csv_file = tmp_path / "feed.csv"
    csv_file.write_text(
        "source_product_id,title,source_url,category,price_minor\n"
        "SKU-P1,Pending Item,https://example.com/p1,tops,1000\n",
        encoding="utf-8",
    )

    sync_service = CatalogSyncService(session_factory)
    with pytest.raises(ValidationError) as exc:
        await sync_service.import_csv_feed(csv_file, source_id, merchant_id)
    assert exc.value.field == "source_id"


@pytest.mark.asyncio
async def test_import_csv_cli_execution_success_and_failures(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Test import_csv CLI run() on fixture input, missing file, and partial errors."""
    import argparse
    import json
    from scripts.catalog.import_csv import run as cli_run

    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="CLI Test Store", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="feed_url",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="hotlink",
        )
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    # 1. Missing file -> exit code 2
    missing_args = argparse.Namespace(
        file=tmp_path / "nonexistent.csv",
        source_id=source_id,
        merchant_id=merchant_id,
        report=tmp_path / "report_missing.json",
    )
    assert await cli_run(missing_args, session_factory=session_factory) == 2

    # 2. Valid fixture file -> exit code 0 and valid report
    valid_csv = tmp_path / "valid.csv"
    valid_csv.write_text(
        "source_product_id,title,source_url,category,price_minor\n"
        "SKU-CLI-1,CLI Linen Shirt,https://partner.example/cli-1,tops,129900\n",
        encoding="utf-8",
    )
    report_file = tmp_path / "report_valid.json"
    valid_args = argparse.Namespace(
        file=valid_csv,
        source_id=source_id,
        merchant_id=merchant_id,
        report=report_file,
    )
    code = await cli_run(valid_args, session_factory=session_factory)
    assert code == 0
    assert report_file.exists()
    report_data = json.loads(report_file.read_text(encoding="utf-8"))
    assert report_data["imported"] == 1
    assert report_data["failed"] == 0

    # 3. Feed with row error -> exit code 1
    mixed_csv = tmp_path / "mixed.csv"
    mixed_csv.write_text(
        "source_product_id,title,source_url,category,price_minor\n"
        "SKU-CLI-OK,Good Item,https://partner.example/cli-ok,tops,1000\n"
        "SKU-CLI-BAD,Bad Item,https://partner.example/cli-bad,invalid_category,1000\n",
        encoding="utf-8",
    )
    mixed_report = tmp_path / "report_mixed.json"
    mixed_args = argparse.Namespace(
        file=mixed_csv,
        source_id=source_id,
        merchant_id=merchant_id,
        report=mixed_report,
    )
    code_mixed = await cli_run(mixed_args, session_factory=session_factory)
    assert code_mixed == 1
    assert mixed_report.exists()
    mixed_data = json.loads(mixed_report.read_text(encoding="utf-8"))
    assert mixed_data["imported"] == 1
    assert mixed_data["failed"] == 1

