from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from scripts.release.validate_vto_release import (
    validate_gate,
    validate_release,
)


@pytest.fixture
def passing_manifest() -> dict[str, Any]:
    return {
        "release": "fashx-vto-mvp-1.0",
        "environment": "staging",
        "commit": "abc1234567890",
        "measured_at": "2026-11-02T10:00:00Z",
        "gates": {
            "G1": {
                "status": "passed",
                "evidence": ["docs/evidence/g1-e2e.md"],
                "physical_device_verified": True,
                "real_backend_verified": True,
                "real_provider_verified": True,
            },
            "G2": {
                "status": "passed",
                "evidence": ["docs/evidence/g2-quality.md"],
                "metrics": {
                    "vlm_accuracy": 92.5,
                    "ranker_ndcg_at_10": 0.78,
                },
            },
            "G3": {
                "status": "passed",
                "evidence": ["docs/evidence/g3-performance.md"],
                "metrics": {
                    "human_realism_mean": 3.8,
                    "p95_tryon_latency_seconds": 32.0,
                    "load_test_rps": 60.0,
                },
            },
            "G4": {
                "status": "passed",
                "evidence": ["docs/evidence/g4-privacy-rto.md"],
                "metrics": {
                    "privacy_counsel_approval": True,
                    "restore_rto_hours": 2.5,
                },
            },
            "G5": {
                "status": "passed",
                "evidence": ["docs/evidence/g5-commercial.md"],
                "metrics": {
                    "catalog_rights_coverage": 100.0,
                    "vendor_dpa_executed": True,
                },
            },
            "G6": {
                "status": "passed",
                "evidence": ["docs/evidence/g6-pilot.md"],
                "metrics": {
                    "participant_count": 25,
                    "acceptable_realism_rate": 80.0,
                    "unresolved_stop_rules": 0,
                },
            },
        },
    }


def test_passing_manifest_passes_validation(passing_manifest: dict[str, Any]) -> None:
    errors = validate_release(passing_manifest)
    assert errors == []


def test_not_measured_gates_are_rejected(passing_manifest: dict[str, Any]) -> None:
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G1"]["status"] = "not_measured"
    errors = validate_release(manifest)
    assert any("G1: status is not passed" in e for e in errors)


def test_missing_metadata_is_rejected(passing_manifest: dict[str, Any]) -> None:
    # 1. Commit placeholder
    manifest = deepcopy(passing_manifest)
    manifest["commit"] = "REPLACE_WITH_GIT_SHA"
    errors = validate_release(manifest)
    assert any("commit SHA missing or unpopulated placeholder" in e for e in errors)

    # 2. Missing measured_at
    manifest["commit"] = "fedcba987654"
    manifest["measured_at"] = ""
    errors = validate_release(manifest)
    assert any("measured_at timestamp missing" in e for e in errors)


def test_empty_evidence_is_rejected(passing_manifest: dict[str, Any]) -> None:
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G3"]["evidence"] = []
    errors = validate_release(manifest)
    assert any("G3: evidence list is empty" in e for e in errors)


def test_g1_physical_device_verification_required(passing_manifest: dict[str, Any]) -> None:
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G1"]["physical_device_verified"] = False
    errors = validate_release(manifest)
    assert any("G1: physical_device_verified must be True" in e for e in errors)


def test_g2_ml_accuracy_threshold(passing_manifest: dict[str, Any]) -> None:
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G2"]["metrics"]["vlm_accuracy"] = 88.0
    errors = validate_release(manifest)
    assert any("G2: vlm_accuracy must be >= 90" in e for e in errors)

    manifest["gates"]["G2"]["metrics"]["vlm_accuracy"] = 92.0
    manifest["gates"]["G2"]["metrics"]["ranker_ndcg_at_10"] = 0.70
    errors = validate_release(manifest)
    assert any("G2: ranker_ndcg_at_10 must be >= 0.75" in e for e in errors)


def test_g3_visual_and_performance_thresholds(passing_manifest: dict[str, Any]) -> None:
    # Realism < 3.5
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G3"]["metrics"]["human_realism_mean"] = 3.2
    errors = validate_release(manifest)
    assert any("G3: human_realism_mean must be >= 3.5" in e for e in errors)

    # Latency > 45s
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G3"]["metrics"]["p95_tryon_latency_seconds"] = 55.0
    errors = validate_release(manifest)
    assert any("G3: p95_tryon_latency_seconds must be <= 45" in e for e in errors)

    # Load test RPS < 50
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G3"]["metrics"]["load_test_rps"] = 40.0
    errors = validate_release(manifest)
    assert any("G3: load_test_rps must be >= 50" in e for e in errors)


def test_g4_privacy_counsel_and_rto(passing_manifest: dict[str, Any]) -> None:
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G4"]["metrics"]["privacy_counsel_approval"] = False
    errors = validate_release(manifest)
    assert any("G4: privacy_counsel_approval must be True" in e for e in errors)

    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G4"]["metrics"]["restore_rto_hours"] = 6.0
    errors = validate_release(manifest)
    assert any("G4: restore_rto_hours must be <= 4" in e for e in errors)


def test_g5_catalog_rights_and_dpa(passing_manifest: dict[str, Any]) -> None:
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G5"]["metrics"]["catalog_rights_coverage"] = 98.0
    errors = validate_release(manifest)
    assert any("G5: catalog_rights_coverage must be 100%" in e for e in errors)

    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G5"]["metrics"]["vendor_dpa_executed"] = False
    errors = validate_release(manifest)
    assert any("G5: vendor_dpa_executed must be True" in e for e in errors)


def test_g6_closed_pilot_thresholds(passing_manifest: dict[str, Any]) -> None:
    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G6"]["metrics"]["participant_count"] = 10
    errors = validate_release(manifest)
    assert any("G6: participant_count must be >= 20" in e for e in errors)

    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G6"]["metrics"]["acceptable_realism_rate"] = 65.0
    errors = validate_release(manifest)
    assert any("G6: acceptable_realism_rate must be >= 75%" in e for e in errors)

    manifest = deepcopy(passing_manifest)
    manifest["gates"]["G6"]["metrics"]["unresolved_stop_rules"] = 2
    errors = validate_release(manifest)
    assert any("G6: unresolved_stop_rules must be 0" in e for e in errors)


def test_evidence_file_existence_check(tmp_path: Any) -> None:
    gate_data: dict[str, Any] = {
        "status": "passed",
        "evidence": ["non_existent_card.md"],
        "physical_device_verified": True,
        "real_backend_verified": True,
        "real_provider_verified": True,
    }
    errors = validate_gate("G1", gate_data, base_dir=tmp_path)
    assert any("evidence file 'non_existent_card.md' not found on disk" in e for e in errors)

    # When file exists
    valid_file = tmp_path / "valid_card.md"
    valid_file.write_text("Evidence contents", encoding="utf-8")
    gate_data["evidence"] = ["valid_card.md"]
    assert validate_gate("G1", gate_data, base_dir=tmp_path) == []
