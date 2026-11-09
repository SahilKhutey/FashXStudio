from scripts.rc12.beta_gates import (
    REQUIRED_GATES,
    BetaDecision,
    GateEvidence,
    GateStatus,
    evaluate_beta_gates,
)


def sample_evidence(status: GateStatus = GateStatus.PASS) -> dict[str, GateEvidence]:
    return {
        gate_id: GateEvidence(
            gate_id=gate_id,
            status=status,
            evidence_reference=f"evidence/{gate_id}.md",
            reviewed_by="release-reviewer",
            reviewed_at="2026-11-09T10:00:00Z",
        )
        for gate_id in REQUIRED_GATES
    }


def test_missing_gate_holds_public_beta():
    result = evaluate_beta_gates({})
    assert result.decision == BetaDecision.HOLD
    assert set(result.unknown) == set(REQUIRED_GATES)


def test_all_verified_gates_allow_go():
    result = evaluate_beta_gates(sample_evidence())
    assert result.decision == BetaDecision.GO
    assert len(result.passed) == len(REQUIRED_GATES)
    assert not result.failed
    assert not result.unknown


def test_failed_gate_requires_fix():
    records = sample_evidence()
    records["G3"] = GateEvidence(
        gate_id="G3",
        status=GateStatus.FAIL,
        evidence_reference="evidence/G3.md",
        reviewed_by="reviewer",
        reviewed_at="2026-11-09T10:00:00Z",
    )
    result = evaluate_beta_gates(records)
    assert result.decision == BetaDecision.FIX
    assert "G3" in result.failed


def test_gate_without_reviewer_holds():
    records = sample_evidence()
    records["G5"] = GateEvidence(
        gate_id="G5",
        status=GateStatus.PASS,
        evidence_reference="evidence/G5.md",
        reviewed_by=None,  # Missing reviewer
    )
    result = evaluate_beta_gates(records)
    assert result.decision == BetaDecision.HOLD
    assert "G5" in result.unknown
