"""Unit tests for safe image validation, SSRF defense, and rights assessment."""

from fashx.catalog.acquisition.image_validator import SafeImageValidator


def test_scheme_and_extension_validation() -> None:
    # Valid HTTPS
    valid, err = SafeImageValidator.validate_image_url("https://images.example.com/products/shirt.jpg")
    assert valid is True
    assert err is None

    # Invalid HTTP
    valid, err = SafeImageValidator.validate_image_url("http://images.example.com/products/shirt.jpg")
    assert valid is False
    assert "scheme must be 'https'" in err.lower()

    # Invalid extension
    valid, err = SafeImageValidator.validate_image_url("https://images.example.com/products/shirt.pdf")
    assert valid is False
    assert "unsupported image extension" in err.lower()


def test_ssrf_protection_blocks_private_and_loopback_ips() -> None:
    # Loopback
    assert SafeImageValidator.validate_image_url("https://localhost/item.png")[0] is False
    assert SafeImageValidator.validate_image_url("https://127.0.0.1/item.png")[0] is False
    assert SafeImageValidator.validate_image_url("https://0.0.0.0/item.png")[0] is False

    # RFC 1918 Private Ranges
    assert SafeImageValidator.validate_image_url("https://10.0.1.5/item.jpg")[0] is False
    assert SafeImageValidator.validate_image_url("https://192.168.1.100/item.jpg")[0] is False
    assert SafeImageValidator.validate_image_url("https://172.16.0.10/item.jpg")[0] is False

    # Cloud Metadata Service (Link-local)
    assert SafeImageValidator.validate_image_url("https://169.254.169.254/latest/meta-data")[0] is False


def test_evaluate_permissions_independent_eligibility() -> None:
    img_url = "https://images.example.com/sample.jpg"

    # 1. Unapproved source: cannot display or try-on
    res = SafeImageValidator.evaluate_permissions(
        image_url=img_url,
        source_status="pending_approval",
        source_rights_display=True,
        source_rights_tryon=True,
        source_image_policy="mirror",
        item_image_rights="owned",
        item_tryon_rights=True,
    )
    assert res.is_valid is True
    assert res.display_eligible is False
    assert res.tryon_eligible is False

    # 2. Cleared source with display rights, but tryon not granted
    res_display_only = SafeImageValidator.evaluate_permissions(
        image_url=img_url,
        source_status="cleared",
        source_rights_display=True,
        source_rights_tryon=False,
        source_image_policy="mirror",
        item_image_rights="partner_authorized",
        item_tryon_rights=True,
    )
    assert res_display_only.display_eligible is True
    assert res_display_only.tryon_eligible is False

    # 3. Cleared source with both display and tryon rights + mirror policy
    res_full = SafeImageValidator.evaluate_permissions(
        image_url=img_url,
        source_status="cleared",
        source_rights_display=True,
        source_rights_tryon=True,
        source_image_policy="mirror",
        item_image_rights="owned",
        item_tryon_rights=True,
    )
    assert res_full.display_eligible is True
    assert res_full.tryon_eligible is True

    # 4. Tryon requested, but image_policy is hotlink (try-on requires server-side mirror)
    res_hotlink = SafeImageValidator.evaluate_permissions(
        image_url=img_url,
        source_status="cleared",
        source_rights_display=True,
        source_rights_tryon=True,
        source_image_policy="hotlink",
        item_image_rights="owned",
        item_tryon_rights=True,
    )
    assert res_hotlink.display_eligible is True
    assert res_hotlink.tryon_eligible is False
