from __future__ import annotations

from fashx.catalog.enrichment.evidence import (
    compute_evidence_hash,
    merchant_field_evidence,
    title_evidence,
    validate_evidence_reference,
)


def test_compute_evidence_hash() -> None:
    """Verify deterministic SHA-256 hash generation for evidence auditing."""
    h1 = compute_evidence_hash("Oversized")
    h2 = compute_evidence_hash("  oversized  ")
    assert h1 == h2
    assert len(h1) == 64


def test_title_evidence_offsets() -> None:
    """Verify title evidence creation with start and end character offsets."""
    title = "Men's Oversized Graphic T-Shirt"
    matched = "Oversized"
    start = title.index(matched)
    end = start + len(matched)

    ev = title_evidence("sku-1", "rev-1", matched, start, end)
    assert ev.start_offset == start
    assert ev.end_offset == end
    assert ev.evidence_text == "Oversized"
    assert validate_evidence_reference(ev, title) is True


def test_enr_018_invalid_evidence_reference_rejected() -> None:
    """Verify ENR-018: Evidence offsets that do not match source content are rejected."""
    title = "Men's Slim Fit Shirt"
    ev = title_evidence("sku-1", "rev-1", "Oversized", 0, 9)
    # Offset 0..9 in "Men's Slim Fit Shirt" is "Men's Sli", not "Oversized"
    assert validate_evidence_reference(ev, title) is False


def test_merchant_field_evidence() -> None:
    """Verify evidence generation from structured merchant fields."""
    ev = merchant_field_evidence("sku-1", "rev-1", "Fabric", "Cotton Blend")
    assert ev.evidence_type == "MERCHANT_FIELD"
    assert "Fabric: Cotton Blend" in (ev.evidence_text or "")
