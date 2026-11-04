import pytest
from fashx.commerce_wardrobe.application.create_buy_click import validate_retailer_url
from fashx.core.errors import ValidationError


def test_rc06_valid_https_url():
    url = "https://www.myntra.com/shirts/brand/12345/buy"
    allowed = {"myntra.com", "amazon.in"}
    result = validate_retailer_url(url, allowed_hosts=allowed)
    assert result == url


def test_rc06_http_rejected():
    url = "http://www.myntra.com/shirts/brand/12345/buy"
    allowed = {"myntra.com"}
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url(url, allowed_hosts=allowed)
    assert "HTTPS" in str(exc.value)


def test_rc06_empty_url_rejected():
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url("")
    assert "must not be empty" in str(exc.value)


def test_rc06_embedded_credentials_rejected():
    url = "https://user:password@www.myntra.com/product"
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url(url, allowed_hosts={"myntra.com"})
    assert "Credentials are not permitted" in str(exc.value)


def test_rc06_unapproved_host_rejected():
    url = "https://www.unknown-retailer.com/product/123"
    allowed = {"myntra.com", "amazon.in"}
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url(url, allowed_hosts=allowed)
    assert "not approved" in str(exc.value)


def test_rc06_lookalike_host_rejected():
    # Attack pattern 1: Domain as subdomain prefix of malicious domain
    url1 = "https://myntra.com.attacker.com/steal"
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url(url1, allowed_hosts={"myntra.com"})
    assert "not approved" in str(exc.value)

    # Attack pattern 2: Hyphenated prefix
    url2 = "https://attacker-myntra.com/steal"
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url(url2, allowed_hosts={"myntra.com"})
    assert "not approved" in str(exc.value)


def test_rc06_subdomain_allowed():
    url = "https://fashion.store.myntra.com/product/item"
    allowed = {"myntra.com"}
    assert validate_retailer_url(url, allowed_hosts=allowed) == url


def test_rc06_production_fail_closed_without_allowed_hosts():
    url = "https://www.myntra.com/product/item"
    with pytest.raises(ValidationError) as exc:
        validate_retailer_url(url, allowed_hosts=None, is_production=True)
    assert "allowlist must be configured in production" in str(exc.value)
