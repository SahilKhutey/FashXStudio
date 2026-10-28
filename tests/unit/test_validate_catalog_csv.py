from pathlib import Path

import pytest

from scripts.catalog.validate_catalog_csv import validate_catalog_csv


def create_csv(tmp_path: Path, filename: str, header: list[str], rows: list[list[str]]) -> Path:
    p = tmp_path / filename
    lines = [",".join(header)]
    for r in rows:
        lines.append(",".join(r))
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


SAMPLE_HEADER = [
    "source_slug",
    "source_product_id",
    "title",
    "brand",
    "category",
    "subcategory",
    "description",
    "price_minor",
    "currency",
    "in_stock",
    "size_values",
    "product_url",
    "image_url",
    "image_rights",
    "tryon_rights",
]


def test_valid_catalog_csv_passes(tmp_path: Path) -> None:
    rows = [
        [
            "manual-demo",
            "p001",
            "Linen Shirt",
            "Studio",
            "tops",
            "shirt",
            "Classic linen",
            "149900",
            "INR",
            "true",
            "S|M|L",
            "https://example.com/p001",
            "https://images.example.com/p001.jpg",
            "owned",
            "true",
        ]
    ]
    p = create_csv(tmp_path, "valid.csv", SAMPLE_HEADER, rows)
    errors = validate_catalog_csv(p)
    assert len(errors) == 0


def test_missing_required_column_fails(tmp_path: Path) -> None:
    bad_header = [c for c in SAMPLE_HEADER if c != "price_minor"]
    rows = [
        [
            "manual-demo",
            "p001",
            "Linen Shirt",
            "Studio",
            "tops",
            "shirt",
            "Classic linen",
            "INR",
            "true",
            "S|M|L",
            "https://example.com/p001",
            "https://images.example.com/p001.jpg",
            "owned",
            "true",
        ]
    ]
    p = create_csv(tmp_path, "missing_col.csv", bad_header, rows)
    errors = validate_catalog_csv(p)
    assert any("Missing required header columns" in e for e in errors)
    assert any("price_minor" in e for e in errors)


def test_duplicate_product_id_fails(tmp_path: Path) -> None:
    row = [
        "manual-demo",
        "dup-001",
        "Shirt",
        "Brand",
        "tops",
        "shirt",
        "Desc",
        "99900",
        "INR",
        "true",
        "S|M",
        "https://example.com/p",
        "https://images.example.com/p.jpg",
        "owned",
        "true",
    ]
    p = create_csv(tmp_path, "dup.csv", SAMPLE_HEADER, [row, row])
    errors = validate_catalog_csv(p)
    assert any("Duplicate 'source_product_id' 'dup-001'" in e for e in errors)


def test_invalid_category_fails(tmp_path: Path) -> None:
    row = [
        "manual-demo",
        "p002",
        "Shoes",
        "Brand",
        "footwear",
        "sneakers",
        "Desc",
        "99900",
        "INR",
        "true",
        "9|10",
        "https://example.com/p",
        "https://images.example.com/p.jpg",
        "owned",
        "false",
    ]
    p = create_csv(tmp_path, "bad_cat.csv", SAMPLE_HEADER, [row])
    errors = validate_catalog_csv(p)
    assert any("Invalid 'category' 'footwear'" in e for e in errors)


def test_negative_or_zero_price_fails(tmp_path: Path) -> None:
    row_zero = [
        "manual-demo",
        "p003",
        "Shirt",
        "Brand",
        "tops",
        "shirt",
        "Desc",
        "0",
        "INR",
        "true",
        "S|M",
        "https://example.com/p",
        "https://images.example.com/p.jpg",
        "owned",
        "true",
    ]
    p = create_csv(tmp_path, "zero_price.csv", SAMPLE_HEADER, [row_zero])
    errors = validate_catalog_csv(p)
    assert any("'price_minor' must be > 0" in e for e in errors)


def test_non_https_and_localhost_urls_rejected(tmp_path: Path) -> None:
    row_http = [
        "manual-demo",
        "p004",
        "Shirt",
        "Brand",
        "tops",
        "shirt",
        "Desc",
        "129900",
        "INR",
        "true",
        "S|M",
        "http://insecure.example.com/p",
        "https://localhost/image.jpg",
        "owned",
        "true",
    ]
    p = create_csv(tmp_path, "insecure_url.csv", SAMPLE_HEADER, [row_http])
    errors = validate_catalog_csv(p)
    assert any("Scheme must be 'https'" in e for e in errors)
    assert any("Forbidden local/internal host" in e for e in errors)


def test_invalid_image_rights_fails(tmp_path: Path) -> None:
    row = [
        "manual-demo",
        "p005",
        "Shirt",
        "Brand",
        "tops",
        "shirt",
        "Desc",
        "129900",
        "INR",
        "true",
        "S|M",
        "https://example.com/p",
        "https://images.example.com/p.jpg",
        "scraped_web",
        "true",
    ]
    p = create_csv(tmp_path, "bad_rights.csv", SAMPLE_HEADER, [row])
    errors = validate_catalog_csv(p)
    assert any("Invalid 'image_rights' 'scraped_web'" in e for e in errors)


def test_empty_csv_fails(tmp_path: Path) -> None:
    p = tmp_path / "empty.csv"
    p.write_text("", encoding="utf-8")
    errors = validate_catalog_csv(p)
    assert len(errors) > 0


@pytest.mark.asyncio
async def test_import_catalog_csv_dry_run_and_apply(tmp_path: Path) -> None:
    from scripts.catalog.import_catalog_csv import import_catalog_csv

    row = [
        "test-demo",
        "demo-001",
        "Classic Linen Shirt",
        "Test Studio",
        "tops",
        "shirt",
        "Breathable relaxed linen button-down shirt; white; regular fit",
        "149900",
        "INR",
        "true",
        "S|M|L",
        "https://example.com/demo-001",
        "https://images.example.com/demo-001.jpg",
        "owned",
        "true",
    ]
    p = create_csv(tmp_path, "import_test.csv", SAMPLE_HEADER, [row])

    # 1. Dry-run mode
    dry_report = await import_catalog_csv(
        p,
        apply=False,
        db_url="sqlite+aiosqlite:///:memory:",
        auto_register_source=True,
    )
    assert dry_report.total_rows == 1
    assert dry_report.inserted == 1
    assert dry_report.rejected == 0
    assert dry_report.quality_passed is True
    assert dry_report.quality_score == 1.0

    # 2. Apply mode
    apply_report = await import_catalog_csv(
        p,
        apply=True,
        db_url="sqlite+aiosqlite:///:memory:",
        auto_register_source=True,
    )
    assert apply_report.total_rows == 1
    assert apply_report.inserted == 1
    assert apply_report.rejected == 0
    assert apply_report.quality_passed is True
    assert apply_report.quality_score == 1.0

