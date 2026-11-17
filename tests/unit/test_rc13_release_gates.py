import hashlib
import json
from pathlib import Path

from scripts.rc13.evaluate_release_gates import (
    REQUIRED_GATES,
    GateEvidence,
    GateStatus,
    MarketDecision,
    evaluate_release_gates,
    load_gates_from_json,
)


def sample_evidence(status: GateStatus = GateStatus.PASS) -> dict[str, GateEvidence]:
    return {
        gate_id: GateEvidence(
            gate_id=gate_id,
            status=status,
            evidence_reference="docs/reengineering/RC13/fixtures/sample_evidence.json",
            reviewed_by="founder",
            reviewed_at="2026-11-09T10:00:00Z",
            is_synthetic=False,
        )
        for gate_id in REQUIRED_GATES
    }


def test_all_gates_pass_returns_go():
    records = sample_evidence(GateStatus.PASS)
    res = evaluate_release_gates(records, verify_references_on_disk=True)
    assert res.decision == MarketDecision.GO
    assert len(res.passed) == len(REQUIRED_GATES)
    assert not res.failed
    assert not res.unknown


def test_placeholder_reviewer_holds():
    records = sample_evidence(GateStatus.PASS)
    records["G3"] = GateEvidence(
        gate_id="G3",
        status=GateStatus.PASS,
        evidence_reference="docs/reengineering/RC13/fixtures/sample_evidence.json",
        reviewed_by="unassigned",  # Placeholder reviewer disallowed
    )
    res = evaluate_release_gates(records)
    assert res.decision == MarketDecision.HOLD
    assert "G3" in res.unknown


def test_missing_evidence_file_on_disk_holds():
    records = sample_evidence(GateStatus.PASS)
    records["G4"] = GateEvidence(
        gate_id="G4",
        status=GateStatus.PASS,
        evidence_reference="docs/evidence/non_existent_file.md",
        reviewed_by="founder",
    )
    res = evaluate_release_gates(records, verify_references_on_disk=True)
    assert res.decision == MarketDecision.HOLD
    assert "G4" in res.unknown


def test_any_gate_fail_returns_fix():
    records = sample_evidence(GateStatus.PASS)
    records["G4"] = GateEvidence(
        gate_id="G4",
        status=GateStatus.FAIL,
        evidence_reference="docs/reengineering/RC13/fixtures/sample_evidence.json",
        reviewed_by="founder",
        reviewed_at="2026-11-09T10:00:00Z",
    )
    res = evaluate_release_gates(records)
    assert res.decision == MarketDecision.FIX
    assert "G4" in res.failed


def test_missing_gate_returns_hold():
    records = sample_evidence(GateStatus.PASS)
    del records["G6"]  # Missing real pilot gate
    res = evaluate_release_gates(records)
    assert res.decision == MarketDecision.HOLD
    assert "G6" in res.unknown


def test_empty_records_returns_hold():
    res = evaluate_release_gates({})
    assert res.decision == MarketDecision.HOLD
    assert set(res.unknown) == set(REQUIRED_GATES)


def test_synthetic_gate_returns_hold():
    records = sample_evidence(GateStatus.PASS)
    records["G6"] = GateEvidence(
        gate_id="G6",
        status=GateStatus.PASS,
        evidence_reference="docs/reengineering/RC13/fixtures/sample_evidence.json",
        reviewed_by="founder",
        is_synthetic=True,
    )
    res = evaluate_release_gates(records)
    assert res.decision == MarketDecision.HOLD
    assert "G6" in res.unknown


def test_load_gates_from_json():
    raw_data: dict[str, dict[str, str | bool | None]] = {
        "G1": {
            "status": "pass",
            "evidence_reference": "docs/reengineering/RC13/fixtures/sample_evidence.json",
            "reviewed_by": "qa",
            "is_synthetic": False,
        },
        "G2": {
            "status": "unknown",
        },
    }
    loaded = load_gates_from_json(raw_data)
    assert "G1" in loaded
    assert loaded["G1"].status == GateStatus.PASS
    assert loaded["G2"].status == GateStatus.UNKNOWN


# --- Enhanced Evidence Authentication Tests ---


def _setup_authenticated_evidence(tmp_path: Path):
    auth_dir = tmp_path / "docs" / "evidence"
    auth_dir.mkdir(parents=True, exist_ok=True)
    src_file = tmp_path / "source_measurement.txt"
    src_file.write_text("authentic_metric_data", encoding="utf-8")
    src_hash = hashlib.sha256(src_file.read_bytes()).hexdigest()

    evidence_map: dict[str, GateEvidence] = {}
    for gate in REQUIRED_GATES:
        ev_file = auth_dir / f"ev_{gate}.json"
        record = {
            "evidence_id": f"EV-{gate}-001",
            "gate_id": gate,
            "type": "technical",
            "status": "pass",
            "collected_by": "founder_authenticated",
            "collected_at": "2026-11-10T12:00:00Z",
            "source_file": str(src_file),
            "checksum": src_hash,
            "is_synthetic": False,
        }
        ev_file.write_text(json.dumps([record]), encoding="utf-8")
        evidence_map[gate] = GateEvidence(
            gate_id=gate,
            status=GateStatus.PASS,
            evidence_reference=str(ev_file),
            reviewed_by="founder_authenticated",
            reviewed_at="2026-11-10T14:00:00Z",
            is_synthetic=False,
        )
    return auth_dir, src_file, evidence_map


def test_authenticate_evidence_all_pass_returns_go(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.GO
    assert len(res.passed) == 6
    assert not res.failed
    assert not res.unknown


def test_evidence_path_outside_authorized_dir_holds(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    outside_file = tmp_path / "outside_evidence.json"
    outside_file.write_text(Path(evidence_map["G1"].evidence_reference).read_text(encoding="utf-8"))

    evidence_map["G1"] = GateEvidence(
        gate_id="G1",
        status=GateStatus.PASS,
        evidence_reference=str(outside_file),
        reviewed_by="founder",
        reviewed_at="2026-11-10T14:00:00Z",
    )
    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.HOLD
    assert "G1" in res.unknown
    assert any("evidence_path_unauthorized" in r for r in res.reasons)


def test_missing_evidence_file_holds_in_auth(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    missing_file = auth_dir / "non_existent.json"
    evidence_map["G2"] = GateEvidence(
        gate_id="G2",
        status=GateStatus.PASS,
        evidence_reference=str(missing_file),
        reviewed_by="founder",
        reviewed_at="2026-11-10T14:00:00Z",
    )
    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.HOLD
    assert "G2" in res.unknown
    assert any("evidence_file_not_found" in r for r in res.reasons)


def test_incorrect_sha256_checksum_holds(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    ev_file = Path(evidence_map["G3"].evidence_reference)
    content = json.loads(ev_file.read_text(encoding="utf-8"))
    content[0]["checksum"] = "badhash" * 8
    ev_file.write_text(json.dumps(content), encoding="utf-8")

    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.HOLD
    assert "G3" in res.unknown
    assert any("evidence_authentication_failed" in r for r in res.reasons)


def test_synthetic_fixture_presented_as_real_evidence_holds(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    ev_file = Path(evidence_map["G4"].evidence_reference)
    content = json.loads(ev_file.read_text(encoding="utf-8"))
    content[0]["is_synthetic"] = True
    ev_file.write_text(json.dumps(content), encoding="utf-8")

    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.HOLD
    assert "G4" in res.unknown
    assert any("synthetic" in r for r in res.reasons)


def test_placeholder_reviewer_holds_in_auth(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    evidence_map["G5"] = GateEvidence(
        gate_id="G5",
        status=GateStatus.PASS,
        evidence_reference=evidence_map["G5"].evidence_reference,
        reviewed_by="placeholder",
        reviewed_at="2026-11-10T14:00:00Z",
    )
    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.HOLD
    assert "G5" in res.unknown
    assert any("missing_or_placeholder_reviewer" in r for r in res.reasons)


def test_missing_or_future_review_timestamp_holds(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    # Missing reviewed_at
    evidence_map["G5"] = GateEvidence(
        gate_id="G5",
        status=GateStatus.PASS,
        evidence_reference=evidence_map["G5"].evidence_reference,
        reviewed_by="founder",
        reviewed_at=None,
    )
    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.HOLD
    assert "G5" in res.unknown
    assert any("missing_reviewed_at" in r for r in res.reasons)

    # Future reviewed_at
    evidence_map["G5"] = GateEvidence(
        gate_id="G5",
        status=GateStatus.PASS,
        evidence_reference=evidence_map["G5"].evidence_reference,
        reviewed_by="founder",
        reviewed_at="2099-01-01T00:00:00Z",
    )
    res2 = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res2.decision == MarketDecision.HOLD
    assert "G5" in res2.unknown
    assert any("future_reviewed_at" in r for r in res2.reasons)


def test_evidence_record_does_not_match_gate_id_holds(tmp_path: Path):
    auth_dir, _, evidence_map = _setup_authenticated_evidence(tmp_path)
    ev_file = Path(evidence_map["G6"].evidence_reference)
    content = json.loads(ev_file.read_text(encoding="utf-8"))
    content[0]["gate_id"] = "G1"  # Mismatch: file says G1, but evaluated for G6
    content[0]["evidence_id"] = "EV-G1-OTHER"
    ev_file.write_text(json.dumps(content), encoding="utf-8")

    res = evaluate_release_gates(
        evidence_map,
        authenticate_evidence=True,
        authorized_dir=auth_dir,
    )
    assert res.decision == MarketDecision.HOLD
    assert "G6" in res.unknown
    assert any("evidence_record_gate_mismatch" in r for r in res.reasons)
