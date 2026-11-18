"""Record validation rules and constraints for catalog ingestion."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

# Supported ISO 4217 currencies and their minor unit exponents
SUPPORTED_CURRENCIES: dict[str, int] = {
    "INR": 2,
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "JPY": 0,
    "AUD": 2,
    "CAD": 2,
    "SGD": 2,
    "AED": 2,
}

VALID_AVAILABILITIES = {
    "in_stock",
    "out_of_stock",
    "preorder",
    "backorder",
    "discontinued",
    "unknown",
}


@dataclass(frozen=True)
class ValidationIssue:
    """A specific validation failure found on a source product record."""

    code: str
    field: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    """Aggregate result of validating a source product record."""

    valid: bool
    issues: tuple[ValidationIssue, ...]


def normalize_source_product_id(value: str | None) -> str:
    """Normalize and validate provider source product identifier."""
    if not value or not str(value).strip():
        raise ValueError("missing_source_product_id")

    result = unicodedata.normalize("NFKC", str(value)).strip()
    if len(result) > 255:
        raise ValueError("source_product_id_too_long")
    if any(ord(char) < 32 for char in result):
        raise ValueError("invalid_source_product_id")
    return result


def normalize_title(raw: str | None) -> str:
    """Normalize display title with printable unicode and length checks."""
    if not raw or not str(raw).strip():
        raise ValueError("missing_title")

    value = unicodedata.normalize("NFKC", str(raw))
    value = "".join(ch for ch in value if ch.isprintable())
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) < 2:
        raise ValueError("title_too_short")
    if len(value) > 300:
        raise ValueError("title_too_long")
    return value


def validate_product_record(
    product: Any,
    allowed_hosts: set[str] | None = None,
) -> ValidationResult:
    """Execute complete field validation against a raw or semi-normalized product record."""
    issues: list[ValidationIssue] = []

    # 1. Source Product ID
    raw_pid = getattr(product, "source_product_id", None)
    try:
        normalize_source_product_id(raw_pid)
    except ValueError as exc:
        code = "missing_product_id" if "missing" in str(exc) else "invalid_product_id"
        issues.append(ValidationIssue(code=code, field="source_product_id", message=str(exc)))

    # 2. Title
    raw_title = getattr(product, "title", None)
    try:
        normalize_title(raw_title)
    except ValueError as exc:
        code = "invalid_title"
        issues.append(ValidationIssue(code=code, field="title", message=str(exc)))

    # 3. Currency
    currency = getattr(product, "currency", None)
    if not currency or not str(currency).strip():
        issues.append(
            ValidationIssue(
                code="missing_currency", field="currency", message="Currency is required"
            )
        )
    elif str(currency).upper().strip() not in SUPPORTED_CURRENCIES:
        issues.append(
            ValidationIssue(
                code="unsupported_currency",
                field="currency",
                message=f"Currency '{currency}' is unsupported",
            )
        )

    # 4. Price
    raw_price = getattr(product, "price_minor", None)
    if raw_price is None:
        issues.append(
            ValidationIssue(code="invalid_price", field="price_minor", message="Price is missing")
        )
    elif isinstance(raw_price, (int, float, Decimal)):
        if int(raw_price) <= 0:
            issues.append(
                ValidationIssue(
                    code="invalid_price", field="price_minor", message="Price must be positive"
                )
            )
    else:
        issues.append(
            ValidationIssue(
                code="invalid_price", field="price_minor", message="Price is not a valid number"
            )
        )

    # 5. Category
    category = getattr(product, "category", None)
    if not category or str(category).strip() in {"", "unmapped", "unknown", "none"}:
        issues.append(
            ValidationIssue(
                code="category_unmapped",
                field="category",
                message="Product category is missing or unmapped",
            )
        )

    # 6. Product URL & Allowed Domains
    url = getattr(product, "product_url", None)
    if url and str(url).strip():
        try:
            parsed = urlparse(str(url).strip())
            if parsed.scheme.lower() != "https":
                issues.append(
                    ValidationIssue(
                        code="invalid_product_url",
                        field="product_url",
                        message=f"Product URL scheme must be https, got '{parsed.scheme}'",
                    )
                )
            elif not parsed.netloc:
                issues.append(
                    ValidationIssue(
                        code="invalid_product_url",
                        field="product_url",
                        message="Product URL has missing netloc/hostname",
                    )
                )
            elif "@" in parsed.netloc:
                issues.append(
                    ValidationIssue(
                        code="invalid_product_url",
                        field="product_url",
                        message="Product URL must not contain embedded user credentials",
                    )
                )
            elif allowed_hosts:
                host = parsed.netloc.split(":")[0].lower()
                # Check exact or subdomain match
                if not any(host == ah or host.endswith(f".{ah}") for ah in allowed_hosts):
                    issues.append(
                        ValidationIssue(
                            code="unapproved_domain",
                            field="product_url",
                            message=f"Product URL host '{host}' not in approved hosts: {allowed_hosts}",
                        )
                    )
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    code="invalid_product_url",
                    field="product_url",
                    message=f"Failed to parse product URL: {exc}",
                )
            )

    return ValidationResult(
        valid=len(issues) == 0,
        issues=tuple(issues),
    )
