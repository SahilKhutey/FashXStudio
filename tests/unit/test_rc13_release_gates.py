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
            evidence_reference=f"docs/evidence/{gate_id}.md",
            reviewed_by="founder",
            reviewed_at="2026-11-09T10:00:00Z",
            is_synthetic=False,
        )
        for gate_id in REQUIRED_GATES
    }


def test_all_gates_pass_returns_go():
    records = sample_evidence(GateStatus.PASS)
    res = evaluate_release_gates(records)
    assert res.decision == MarketDecision.GO
    assert len(res.passed) == len(REQUIRED_GATES)
    assert not res.failed
    assert not res.unknown


def test_any_gate_fail_returns_fix():
    records = sample_evidence(GateStatus.PASS)
    records["G4"] = GateEvidence(
        gate_id="G4",
        status=GateStatus.FAIL,
        evidence_reference="docs/evidence/G4.md",
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
    assert any("gate_G6_unmeasured_or_missing" in r for r in res.reasons)


def test_empty_records_returns_hold():
    res = evaluate_release_gates({})
    assert res.decision == MarketDecision.HOLD
    assert set(res.unknown) == set(REQUIRED_GATES)


def test_missing_reviewer_or_ref_returns_hold():
    records = sample_evidence(GateStatus.PASS)
    records["G5"] = GateEvidence(
        gate_id="G5",
        status=GateStatus.PASS,
        evidence_reference=None,  # Missing evidence card
        reviewed_by="founder",
    )
    res = evaluate_release_gates(records)
    assert res.decision == MarketDecision.HOLD
    assert "G5" in res.unknown

    records["G5"] = GateEvidence(
        gate_id="G5",
        status=GateStatus.PASS,
        evidence_reference="docs/evidence/G5.md",
        reviewed_by=None,  # Missing reviewer
    )
    res2 = evaluate_release_gates(records)
    assert res2.decision == MarketDecision.HOLD
    assert "G5" in res2.unknown


def test_synthetic_gate_returns_hold():
    records = sample_evidence(GateStatus.PASS)
    records["G6"] = GateEvidence(
        gate_id="G6",
        status=GateStatus.PASS,
        evidence_reference="docs/evidence/G6.md",
        reviewed_by="founder",
        is_synthetic=True,  # Synthetic data rejected for production gate
    )
    res = evaluate_release_gates(records)
    assert res.decision == MarketDecision.HOLD
    assert "G6" in res.unknown
    assert any("gate_G6_synthetic_evidence_rejected" in r for r in res.reasons)


def test_load_gates_from_json():
    raw_data: dict[str, dict[str, str | bool | None]] = {
        "G1": {
            "status": "pass",
            "evidence_reference": "docs/evidence/G1.md",
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
