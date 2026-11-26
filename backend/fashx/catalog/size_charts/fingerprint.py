"""Deterministic cryptographic fingerprinting for merchant size charts for Phase 08.1."""

from __future__ import annotations

import hashlib
import json

from .schemas import SizeChartRevisionCreate

FINGERPRINT_VERSION = "v1"


def chart_fingerprint(
    chart: SizeChartRevisionCreate,
) -> str:
    """Calculate a deterministic SHA-256 fingerprint of a size chart's content.

    Rules:
    1. Retrieval timestamps and provenance metadata ('source') are excluded so repeated
       ingestion of identical merchant data does not create unnecessary revisions.
    2. Rows, size labels, and normalized measurements are sorted and canonicalized.
    """
    payload = chart.model_dump(mode="json")
    payload.pop("source", None)

    # Sort rows by size label for canonical ordering
    if "rows" in payload and isinstance(payload["rows"], list):
        payload["rows"] = sorted(payload["rows"], key=lambda r: str(r.get("merchant_size", "")).upper())
        for row in payload["rows"]:
            if "measurements" in row and isinstance(row["measurements"], list):
                row["measurements"] = sorted(
                    row["measurements"],
                    key=lambda m: str(m.get("field_code") or m.get("field") or "").upper(),
                )

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


compute_size_chart_fingerprint = chart_fingerprint
