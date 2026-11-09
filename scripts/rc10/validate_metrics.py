"""RC10 metric record validation and pilot eligibility verifier."""
from __future__ import annotations

from datetime import datetime
from typing import Any

ALLOWED_EVIDENCE = {
    "real",
    "synthetic",
    "simulated",
    "test",
}


def validate_metric_record(record: dict[str, Any]) -> list[str]:
    """Validates metric record schema, non-null requirements, evidence classification, and timestamp validity."""
    errors: list[str] = []
    required = (
        "metric_name",
        "value",
        "sample_size",
        "period_start",
        "period_end",
        "extracted_at",
        "evidence_type",
        "source_reference",
    )
    for field in required:
        if record.get(field) is None:
            errors.append(f"missing_{field}")
    if errors:
        return errors

    if record["evidence_type"] not in ALLOWED_EVIDENCE:
        errors.append("invalid_evidence_type")

    if record["sample_size"] < 0:
        errors.append("negative_sample_size")

    for dt_field in ("period_start", "period_end", "extracted_at"):
        val = record.get(dt_field)
        if val:
            try:
                datetime.fromisoformat(str(val))
            except Exception:
                errors.append(f"invalid_{dt_field}")

    return errors


def is_eligible_for_pilot_claim(record: dict[str, Any]) -> bool:
    """Verifies that a metric record is rigorously validated and originates from real user evidence."""
    errors = validate_metric_record(record)
    if errors:
        return False
    if record.get("evidence_type") != "real":
        return False
    if record.get("sample_size", 0) <= 0:
        return False
    return True
