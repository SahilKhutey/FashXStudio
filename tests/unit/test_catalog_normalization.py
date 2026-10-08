from fashx.catalog.normalization.brand_normalizer import BrandNormalizer
from fashx.catalog.normalization.text_normalizer import TextNormalizer


def test_brand_normalizer_resolves_aliases() -> None:
    cases = [
        ("H&M", "H&M", "hm"),
        ("h and m", "H&M", "hm"),
        ("Zara Man", "Zara", "zaraman"),
        ("Levi's", "Levi's", "levis"),
        ("m&s", "Marks & Spencer", "ms"),
        ("Unknown Brand", "Unknown Brand", "unknownbrand"),
    ]
    for raw, expected_canonical, expected_key in cases:
        canonical, key = BrandNormalizer.resolve_brand(raw)
        assert canonical == expected_canonical
        assert key == expected_key


def test_text_normalizer_removes_promotional_tokens() -> None:
    raw = "Slim Fit Cotton Shirt [New Arrival] - 50% Off! (Trending)"
    clean = TextNormalizer.clean_title(raw)
    assert "50% Off" not in clean
    assert "[New Arrival]" not in clean
    assert "(Trending)" not in clean
    assert clean == "Slim Fit Cotton Shirt"


def test_text_normalizer_infers_category_and_fit() -> None:
    res1 = TextNormalizer.infer_category_and_fit("Oxford Casual Shirt Slim Fit")
    assert res1.category == "tops"
    assert res1.subcategory == "casual_shirts"
    assert res1.inferred_fit == "slim"

    res2 = TextNormalizer.infer_category_and_fit("Men Relaxed Fit Chinos Trousers")
    assert res2.category == "bottoms"
    assert res2.subcategory == "chinos"
    assert res2.inferred_fit == "relaxed"

    res3 = TextNormalizer.infer_category_and_fit("Classic Wool Suit Blazer")
    assert res3.category == "outerwear"
    assert res3.subcategory == "blazers"
