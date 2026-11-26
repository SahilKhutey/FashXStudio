"""Unit tests for dataset manifest, permissions, and diversity (Phase 07.7).

Covers DATA-001 through DATA-012 and DIV-001 through DIV-005.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from fashx.tryon.evaluation.contracts import (
    DatasetPartition,
    EvaluationDifficulty,
    EvaluationPair,
    ExpectedOutcome,
    load_manifest_pairs,
)

SAMPLE_PAIR_DATA = {
    "pair_id": "pair-test-001",
    "dataset_version": "vto-benchmark-1.0",
    "participant_id": "participant-pseudo-001",
    "shopper_asset_id": uuid.UUID("11111111-1111-4111-8111-111111111101"),
    "garment_asset_id": uuid.UUID("22222222-2222-4222-8222-222222222201"),
    "canonical_product_id": uuid.UUID("33333333-3333-4333-8333-333333333301"),
    "garment_category": "tshirts",
    "market": "IN",
    "partition": "DEVELOPMENT",
    "height_band": "166-175",
    "body_representation_group": "group-a",
    "skin_tone_annotation": "medium",
    "lighting": "NATURAL_BRIGHT",
    "camera_distance": "FULL_BODY",
    "pose": "FRONT_RELAXED",
    "difficulty": "STANDARD",
    "permission_record_id": "perm-001",
    "eligible_for_live_provider": True,
    "expected_outcome": "INFERENCE",
}


def test_valid_evaluation_pair_creation():
    """DATA-001: Valid pair definition creates immutable model."""
    pair = EvaluationPair(**SAMPLE_PAIR_DATA)
    assert pair.pair_id == "pair-test-001"
    assert pair.garment_category == "tshirts"
    assert pair.partition == DatasetPartition.DEVELOPMENT
    assert pair.expected_outcome == ExpectedOutcome.INFERENCE


def test_missing_permission_record_raises_error():
    """DATA-002: Missing permission_record_id raises validation error."""
    invalid_data = SAMPLE_PAIR_DATA.copy()
    del invalid_data["permission_record_id"]
    with pytest.raises(ValidationError):
        EvaluationPair(**invalid_data)


def test_extra_field_forbidden():
    """DATA-003: Extra unapproved fields raise validation error (extra=forbid)."""
    invalid_data = SAMPLE_PAIR_DATA.copy()
    invalid_data["unapproved_private_field"] = "leaked_data"
    with pytest.raises(ValidationError):
        EvaluationPair(**invalid_data)


def test_manifest_v1_jsonl_loading():
    """DATA-004 & DIV-001..005: Manifest loads cleanly and reflects category diversity."""
    manifest_path = Path("datasets/vto/manifest.v1.jsonl")
    assert manifest_path.exists(), "Manifest file must exist"

    pairs = load_manifest_pairs(manifest_path)
    assert len(pairs) >= 7, "Manifest should contain benchmark sample pairs"

    categories = {p.garment_category for p in pairs}
    assert "tshirts" in categories
    assert "basic_kurtas" in categories
    assert "dresses" in categories
    assert "sarees" in categories

    # Verify negative cases
    negative_pairs = [p for p in pairs if p.difficulty == EvaluationDifficulty.NEGATIVE]
    assert len(negative_pairs) >= 1
    assert negative_pairs[0].expected_outcome == ExpectedOutcome.REJECT_INPUT
    assert negative_pairs[0].eligible_for_live_provider is False

    # Verify holdout partition exists
    holdout_pairs = [p for p in pairs if p.partition == DatasetPartition.HOLDOUT_TEST]
    assert len(holdout_pairs) >= 1


def test_manifest_missing_file_raises():
    """DATA-005: Non-existent manifest path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_manifest_pairs("non_existent_path.jsonl")
