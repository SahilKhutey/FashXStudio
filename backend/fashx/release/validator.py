"""Release gate validation module for FashXStudio Virtual Try-On MVP.

Verifies that evidence manifests contain all required gate sign-offs,
verifiable evidence card paths, and metric thresholds matching docs/release/gates.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

GATES: dict[str, str] = {
    "G1": "End-to-end real-stack journey",
    "G2": "ML quality and VLM accuracy",
    "G3": "Visual quality, latency and load",
    "G4": "Privacy, legal and recovery",
    "G5": "Commercial licences and vendor DPA",
    "G6": "Closed pilot evaluation",
}


def valid_number(value: Any) -> bool:
    """Returns True if value is an int or float and not a boolean."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_gate(
    gate_id: str,
    gate: dict[str, Any],
    base_dir: Path | None = None,
) -> list[str]:
    """Validates an individual release gate against defined thresholds."""
    errors: list[str] = []

    if gate.get("status") != "passed":
        errors.append(f"{gate_id}: status is not passed (got '{gate.get('status')}')")
        return errors

    evidence = gate.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{gate_id}: evidence list is empty")
    else:
        for item in evidence:
            if not isinstance(item, str) or not item.strip():
                errors.append(f"{gate_id}: invalid evidence reference '{item}'")
            elif base_dir:
                evidence_file = base_dir / item
                if not evidence_file.exists():
                    errors.append(f"{gate_id}: evidence file '{item}' not found on disk")

    metrics = gate.get("metrics") or {}

    if gate_id == "G1":
        if gate.get("physical_device_verified") is not True:
            errors.append("G1: physical_device_verified must be True")
        if gate.get("real_backend_verified") is not True:
            errors.append("G1: real_backend_verified must be True")
        if gate.get("real_provider_verified") is not True:
            errors.append("G1: real_provider_verified must be True")

    elif gate_id == "G2":
        vlm_acc = metrics.get("vlm_accuracy")
        if not valid_number(vlm_acc) or vlm_acc < 90:
            errors.append(f"G2: vlm_accuracy must be >= 90 (got {vlm_acc})")
        ndcg = metrics.get("ranker_ndcg_at_10")
        if not valid_number(ndcg) or ndcg < 0.75:
            errors.append(f"G2: ranker_ndcg_at_10 must be >= 0.75 (got {ndcg})")

    elif gate_id == "G3":
        realism = metrics.get("human_realism_mean")
        if not valid_number(realism) or realism < 3.5:
            errors.append(f"G3: human_realism_mean must be >= 3.5 (got {realism})")
        latency = metrics.get("p95_tryon_latency_seconds")
        if not valid_number(latency) or latency > 45.0:
            errors.append(f"G3: p95_tryon_latency_seconds must be <= 45 (got {latency})")
        rps = metrics.get("load_test_rps")
        if not valid_number(rps) or rps < 50.0:
            errors.append(f"G3: load_test_rps must be >= 50 (got {rps})")

    elif gate_id == "G4":
        if metrics.get("privacy_counsel_approval") is not True:
            errors.append("G4: privacy_counsel_approval must be True")
        rto = metrics.get("restore_rto_hours")
        if not valid_number(rto) or rto > 4.0:
            errors.append(f"G4: restore_rto_hours must be <= 4 (got {rto})")

    elif gate_id == "G5":
        rights = metrics.get("catalog_rights_coverage")
        if not valid_number(rights) or rights < 100.0:
            errors.append(f"G5: catalog_rights_coverage must be 100% (got {rights})")
        if metrics.get("vendor_dpa_executed") is not True:
            errors.append("G5: vendor_dpa_executed must be True")

    elif gate_id == "G6":
        participants = metrics.get("participant_count")
        if not valid_number(participants) or participants < 20:
            errors.append(f"G6: participant_count must be >= 20 (got {participants})")
        acceptable_rate = metrics.get("acceptable_realism_rate")
        if not valid_number(acceptable_rate) or acceptable_rate < 75.0:
            errors.append(f"G6: acceptable_realism_rate must be >= 75% (got {acceptable_rate})")
        stop_rules = metrics.get("unresolved_stop_rules")
        if not valid_number(stop_rules) or stop_rules != 0:
            errors.append(f"G6: unresolved_stop_rules must be 0 (got {stop_rules})")

    return errors


def validate_release(
    manifest: dict[str, Any],
    base_dir: Path | None = None,
) -> list[str]:
    """Validates the complete evidence manifest across all 6 release gates."""
    errors: list[str] = []

    release_name = manifest.get("release")
    if not isinstance(release_name, str) or not release_name.strip():
        errors.append("Metadata: release name missing or invalid")

    environment = manifest.get("environment")
    if not isinstance(environment, str) or not environment.strip():
        errors.append("Metadata: environment missing or invalid")

    commit = manifest.get("commit")
    if not isinstance(commit, str) or not commit.strip() or "REPLACE_WITH" in commit:
        errors.append("Metadata: commit SHA missing or unpopulated placeholder")

    measured_at = manifest.get("measured_at")
    if not isinstance(measured_at, str) or not measured_at.strip():
        errors.append("Metadata: measured_at timestamp missing")

    gates = manifest.get("gates")
    if not isinstance(gates, dict):
        errors.append("Manifest: missing 'gates' object")
        return errors

    for gate_id in GATES:
        if gate_id not in gates:
            errors.append(f"Manifest: missing gate definition '{gate_id}'")
        else:
            errors.extend(validate_gate(gate_id, gates[gate_id], base_dir=base_dir))

    return errors
