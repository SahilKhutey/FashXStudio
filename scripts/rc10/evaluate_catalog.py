"""RC10 catalog quality and freshness evaluator."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class CatalogQualityResult:
    passed: bool
    score: float
    errors: tuple[str, ...]


def evaluate_product(
    product: dict[str, Any],
    *,
    max_price_age_hours: int = 24,
    reference_time: datetime | None = None,
) -> CatalogQualityResult:
    """Evaluates catalog product adherence to provenance, clearance, and freshness standards."""
    errors: list[str] = []
    required = (
        "merchant_id",
        "source_product_id",
        "canonical_product_id",
        "category",
        "image_reference",
        "source_clearance",
        "price",
        "currency",
        "price_updated_at",
    )
    for field in required:
        if product.get(field) in (None, ""):
            errors.append(f"missing_{field}")

    if "missing_image_reference" in errors:
        errors.append("missing_image")

    # Source clearance validation
    if not product.get("source_clearance"):
        errors.append("source_not_cleared")

    # Image reference presence
    if not product.get("image_reference"):
        if "missing_image" not in errors:
            errors.append("missing_image")

    # Price validation
    price = product.get("price")
    if price is not None and isinstance(price, (int, float)) and price <= 0:
        errors.append("invalid_price")

    # Price freshness validation
    price_updated_at = product.get("price_updated_at")
    if price_updated_at:
        try:
            if isinstance(price_updated_at, str):
                updated_dt = datetime.fromisoformat(price_updated_at)
            else:
                updated_dt = price_updated_at
            if updated_dt.tzinfo is None:
                updated_dt = updated_dt.replace(tzinfo=UTC)

            now = reference_time or datetime(2026, 11, 5, 5, 0, tzinfo=UTC)
            age_hours = (now - updated_dt).total_seconds() / 3600.0
            if age_hours > max_price_age_hours:
                errors.append("stale_price")
        except Exception:
            errors.append("invalid_price_updated_at")

    # Calculate score
    unique_errors = tuple(sorted(set(errors)))
    if unique_errors:
        total_checks = len(required) + 3
        score = max(0.0, 1.0 - (len(unique_errors) / total_checks))
        return CatalogQualityResult(
            passed=False,
            score=score,
            errors=unique_errors,
        )

    return CatalogQualityResult(
        passed=True,
        score=1.0,
        errors=(),
    )
