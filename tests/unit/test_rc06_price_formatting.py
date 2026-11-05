import pytest


def format_price(amount_minor: int, currency: str = "INR") -> str:
    """Format minor currency unit to human-readable string with currency symbol/code."""
    if amount_minor < 0:
        raise ValueError("Price minor must be non-negative")

    major = amount_minor / 100
    if currency.upper() == "INR":
        if major.is_integer():
            return f"₹{int(major):,}"
        return f"₹{major:,.2f}"
    elif currency.upper() == "USD":
        return f"${major:,.2f}"
    elif currency.upper() == "EUR":
        return f"€{major:,.2f}"
    return f"{currency.upper()} {major:,.2f}"


def test_rc06_inr_formatting():
    assert format_price(129900, "INR") == "₹1,299"
    assert format_price(99900, "INR") == "₹999"
    assert format_price(129950, "INR") == "₹1,299.50"
    assert format_price(0, "INR") == "₹0"


def test_rc06_multi_currency_formatting():
    assert format_price(4999, "USD") == "$49.99"
    assert format_price(12500, "EUR") == "€125.00"
    assert format_price(500000, "GBP") == "GBP 5,000.00"


def test_rc06_negative_price_rejected():
    with pytest.raises(ValueError):
        format_price(-100, "INR")
