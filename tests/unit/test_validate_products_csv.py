from pathlib import Path

from scripts.catalog.validate_products_csv import validate_csv_file, validate_row


def test_validate_row_valid_input() -> None:
    row = {
        "source_product_id": "SKU-001",
        "title": "Oxford Cotton Shirt",
        "source_url": "https://example.com/items/001",
        "category": "tops",
        "price_minor": "199900",
        "currency": "INR",
        "in_stock": "true",
    }
    errors = validate_row(row, line=2)
    assert errors == []


def test_validate_row_rejects_missing_fields() -> None:
    row = {
        "source_product_id": "",
        "title": " ",
        "source_url": "not-a-url",
        "category": "unknown-cat",
        "price_minor": "-100",
        "currency": "USD",
        "in_stock": "invalid-bool",
    }
    errors = validate_row(row, line=5)
    assert any("source_product_id is required" in e for e in errors)
    assert any("title is required" in e for e in errors)
    assert any("valid HTTPS URL" in e for e in errors)
    assert any("price_minor cannot be negative" in e for e in errors)
    assert any("currency must be 'INR'" in e for e in errors)
    assert any("not in approved taxonomy" in e for e in errors)
    assert any("in_stock must be a boolean" in e for e in errors)


def test_validate_csv_file_detects_duplicates(tmp_path: Path) -> None:
    csv_file = tmp_path / "dup.csv"
    csv_file.write_text(
        "source_product_id,title,source_url,category,price_minor,currency,in_stock\n"
        "SKU-1,Shirt 1,https://example.com/1,tops,1000,INR,true\n"
        "SKU-1,Shirt 2,https://example.com/2,tops,2000,INR,true\n",
        encoding="utf-8",
    )
    is_valid, errors, total_rows = validate_csv_file(csv_file)
    assert not is_valid
    assert total_rows == 2
    assert any("duplicate source_product_id 'SKU-1'" in e for e in errors)


def test_validate_csv_file_valid_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "valid.csv"
    csv_file.write_text(
        "source_product_id,title,source_url,category,price_minor,currency,in_stock\n"
        "SKU-1,Shirt 1,https://example.com/1,tops,1000,INR,true\n"
        "SKU-2,Pants 1,https://example.com/2,bottoms,2000,INR,false\n",
        encoding="utf-8",
    )
    is_valid, errors, total_rows = validate_csv_file(csv_file)
    assert is_valid
    assert errors == []
    assert total_rows == 2
