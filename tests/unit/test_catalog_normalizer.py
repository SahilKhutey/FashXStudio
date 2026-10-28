"""Unit tests for the catalog normalization pipeline."""

from fashx.catalog.acquisition.contract import SourceProduct
from fashx.catalog.acquisition.normalizer import CatalogNormalizer


def test_category_normalization_mappings() -> None:
    # Tops mapping
    cat, subcat = CatalogNormalizer.normalize_category("Men's Apparel", "Casual Linen Button-Down Shirt")
    assert cat == "tops"
    assert subcat == "shirt"

    cat, subcat = CatalogNormalizer.normalize_category("T-shirts & Polos", "Graphic Cotton Tee")
    assert cat == "tops"
    assert subcat == "tshirt"

    # Bottoms mapping
    cat, subcat = CatalogNormalizer.normalize_category("Clothing", "Men Slim Fit Stretch Denim Jeans")
    assert cat == "bottoms"
    assert subcat == "jeans"

    cat, subcat = CatalogNormalizer.normalize_category("Pants", "Pleated Straight Trousers")
    assert cat == "bottoms"
    assert subcat == "trousers"

    # Dresses mapping
    cat, subcat = CatalogNormalizer.normalize_category("Women Fashion", "Floral Print Tiered Maxi Dress")
    assert cat == "dresses"
    assert subcat == "dress"

    # Outerwear mapping
    cat, subcat = CatalogNormalizer.normalize_category("Jackets", "Canvas Utility Chore Jacket")
    assert cat == "outerwear"
    assert subcat == "jacket"


def test_brand_normalization() -> None:
    assert CatalogNormalizer.normalize_brand("Fabindia Pvt Ltd") == "Fabindia"
    assert CatalogNormalizer.normalize_brand("Raymond LLC") == "Raymond"
    assert CatalogNormalizer.normalize_brand(None, title="Westside Men Linen Shirt") == "Westside"
    assert CatalogNormalizer.normalize_brand(None, title="") == "Unknown"


def test_price_normalization() -> None:
    # Rupee float to paise minor
    assert CatalogNormalizer.normalize_price_minor(1499.50) == 149950
    # Already integer paise
    assert CatalogNormalizer.normalize_price_minor(149900) == 149900
    # Zero or negative
    assert CatalogNormalizer.normalize_price_minor(-500) == 0


def test_size_normalization() -> None:
    assert CatalogNormalizer.normalize_sizes(("s", "m", "l", "xl")) == ("S", "M", "L", "XL")
    assert CatalogNormalizer.normalize_sizes("xs | s | m | l") == ("XS", "S", "M", "L")
    assert CatalogNormalizer.normalize_sizes("28, 30, 32, 34") == ("28", "30", "32", "34")


def test_url_sanitization() -> None:
    raw_url = "https://www.example.com/item/123?utm_source=google&id=123&ref=banner"
    clean = CatalogNormalizer.sanitize_url(raw_url)
    assert "utm_source" not in clean
    assert "ref" not in clean
    assert "id=123" in clean


def test_full_source_product_normalization() -> None:
    raw = SourceProduct(
        source_slug="Amazon",
        source_product_id="SKU-101",
        title="Symbol Men Classic Regular Fit Cotton Shirt",
        category="Men Western Wear",
        subcategory="Shirts",
        brand="Symbol Apparels Pvt Ltd",
        price_minor=1299.00,  # float rupees
        currency="inr",
        product_url="https://amazon.in/dp/SKU-101?utm_source=ad",
        image_url="https://images.amazon.in/SKU-101.jpg?ref=img",
        sizes=("s", "m", "l"),
    )
    norm = CatalogNormalizer.normalize_product(raw)
    assert norm.source_slug == "amazon"
    assert norm.brand == "Symbol Apparels"
    assert norm.category == "tops"
    assert norm.subcategory == "shirt"
    assert norm.price_minor == 129900
    assert norm.currency == "INR"
    assert norm.sizes == ("S", "M", "L")
    assert "utm_source" not in norm.product_url
    assert "ref" not in (norm.image_url or "")
