from __future__ import annotations

import hashlib
from uuid import uuid4

from .contracts import EnrichmentEvidence, EvidenceType


def compute_evidence_hash(text: str) -> str:
    """Calculate a deterministic SHA-256 hash for evidence text verification."""
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


def title_evidence(
    source_record_id: str,
    source_revision: str | None,
    matched_text: str,
    start: int,
    end: int,
    extraction_method: str = "DETERMINISTIC_TITLE_RULE",
) -> EnrichmentEvidence:
    """Generate traceable evidence for title-extracted attributes."""
    return EnrichmentEvidence(
        evidence_id=str(uuid4()),
        evidence_type=EvidenceType.TITLE,
        source_record_id=source_record_id,
        source_revision=source_revision,
        evidence_text=matched_text,
        evidence_hash=compute_evidence_hash(matched_text),
        start_offset=start,
        end_offset=end,
        extraction_method=extraction_method,
    )


def description_evidence(
    source_record_id: str,
    source_revision: str | None,
    matched_text: str,
    start: int,
    end: int,
    extraction_method: str = "DETERMINISTIC_DESCRIPTION_RULE",
) -> EnrichmentEvidence:
    """Generate traceable evidence for description-extracted attributes."""
    return EnrichmentEvidence(
        evidence_id=str(uuid4()),
        evidence_type=EvidenceType.DESCRIPTION,
        source_record_id=source_record_id,
        source_revision=source_revision,
        evidence_text=matched_text,
        evidence_hash=compute_evidence_hash(matched_text),
        start_offset=start,
        end_offset=end,
        extraction_method=extraction_method,
    )


def merchant_field_evidence(
    source_record_id: str,
    source_revision: str | None,
    field_name: str,
    raw_value: str,
) -> EnrichmentEvidence:
    """Generate evidence traceable to structured merchant input fields."""
    return EnrichmentEvidence(
        evidence_id=str(uuid4()),
        evidence_type=EvidenceType.MERCHANT_FIELD,
        source_record_id=source_record_id,
        source_revision=source_revision,
        evidence_text=f"{field_name}: {raw_value}",
        evidence_hash=compute_evidence_hash(raw_value),
        extraction_method="STRUCTURED_MERCHANT_FIELD",
    )


def image_asset_evidence(
    source_record_id: str,
    source_revision: str | None,
    asset_id: str,
    extraction_method: str = "AUTHORIZED_IMAGE_ANALYSIS",
    model_id: str | None = None,
    model_version: str | None = None,
) -> EnrichmentEvidence:
    """Generate traceable evidence for visual attributes derived from an authorized image asset."""
    return EnrichmentEvidence(
        evidence_id=str(uuid4()),
        evidence_type=EvidenceType.IMAGE_ASSET,
        source_record_id=source_record_id,
        source_revision=source_revision,
        asset_id=asset_id,
        extraction_method=extraction_method,
        model_id=model_id,
        model_version=model_version,
    )


def validate_evidence_reference(
    evidence: EnrichmentEvidence,
    source_text: str | None,
) -> bool:
    """Validate that text-based evidence offsets correspond to actual text in the source content."""
    if evidence.evidence_type in {EvidenceType.TITLE, EvidenceType.DESCRIPTION}:
        if not source_text or evidence.evidence_text is None:
            return False
        if evidence.start_offset is not None and evidence.end_offset is not None:
            if evidence.start_offset < 0 or evidence.end_offset > len(source_text):
                return False
            actual_slice = source_text[evidence.start_offset : evidence.end_offset]
            if actual_slice.lower() != evidence.evidence_text.lower():
                return False
        elif evidence.evidence_text.lower() not in source_text.lower():
            return False
    return True
