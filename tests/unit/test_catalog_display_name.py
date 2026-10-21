from uuid import uuid4

from database.models.catalog import CanonicalGarment


def test_display_name_prefers_explicit_display_name() -> None:
    garment = CanonicalGarment(
        id=uuid4(),
        display_name="Custom Silk Blouse",
        title="Ignored Title",
        category="tops",
        subcategory="blouse",
    )
    assert garment.display_name == "Custom Silk Blouse"


def test_display_name_uses_title_when_display_name_absent() -> None:
    garment = CanonicalGarment(
        id=uuid4(),
        title="Embroidered Festive Kurta",
        category="tops",
        subcategory="kurta",
    )
    assert garment.display_name == "Embroidered Festive Kurta"


def test_display_name_falls_back_to_subcategory_when_title_and_display_name_absent() -> None:
    garment = CanonicalGarment(
        id=uuid4(),
        category="tops",
        subcategory="linen_shirt",
    )
    assert garment.display_name == "linen_shirt"


def test_display_name_falls_back_to_category_when_subcategory_and_title_absent() -> None:
    garment = CanonicalGarment(
        id=uuid4(),
        category="dresses",
    )
    assert garment.display_name == "dresses"


def test_display_name_falls_back_when_explicit_display_name_empty() -> None:
    garment = CanonicalGarment(
        id=uuid4(),
        display_name="",
        title="",
        category="bottoms",
        subcategory="cargo_pants",
    )
    assert garment.display_name == "cargo_pants"
