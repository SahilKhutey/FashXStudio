"""Unit tests for the multi-factor CatalogEligibility policy gate."""

from fashx.catalog.eligibility import evaluate_eligibility


def test_fully_eligible_item() -> None:
    res = evaluate_eligibility(
        source_cleared=True,
        display_rights=True,
        image_validated=True,
        tryon_rights=True,
        stock_known=True,
        in_stock=True,
        product_url_valid=True,
        category_valid=True,
        price_valid=True,
    )
    assert res.discoverable is True
    assert res.image_displayable is True
    assert res.tryon_allowed is True
    assert res.purchasable is True
    assert len(res.reasons) == 0


def test_unapproved_source_fails_all_capabilities() -> None:
    res = evaluate_eligibility(
        source_cleared=False,
        display_rights=True,
        image_validated=True,
        tryon_rights=True,
        stock_known=True,
        in_stock=True,
        product_url_valid=True,
        category_valid=True,
        price_valid=True,
    )
    assert res.discoverable is False
    assert res.image_displayable is False
    assert res.tryon_allowed is False
    assert res.purchasable is False
    assert any("Source is not approved" in r for r in res.reasons)


def test_discoverable_without_image_display_or_tryon() -> None:
    # A valid product listing can exist and be discoverable even when image display rights are absent
    res = evaluate_eligibility(
        source_cleared=True,
        display_rights=False,
        image_validated=False,
        tryon_rights=False,
        stock_known=True,
        in_stock=True,
        product_url_valid=True,
        category_valid=True,
        price_valid=True,
    )
    assert res.discoverable is True
    assert res.image_displayable is False
    assert res.tryon_allowed is False
    assert res.purchasable is True
    assert any("Image display rights or byte validation missing" in r for r in res.reasons)


def test_out_of_stock_item_discoverable_but_not_purchasable() -> None:
    res = evaluate_eligibility(
        source_cleared=True,
        display_rights=True,
        image_validated=True,
        tryon_rights=True,
        stock_known=True,
        in_stock=False,  # Out of stock
        product_url_valid=True,
        category_valid=True,
        price_valid=True,
    )
    assert res.discoverable is True
    assert res.image_displayable is True
    assert res.tryon_allowed is True
    assert res.purchasable is False
    assert any("Item is out of stock" in r for r in res.reasons)
