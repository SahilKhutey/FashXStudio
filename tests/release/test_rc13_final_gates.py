"""RC13 Release Gate Integration Test."""
from scripts.rc13.evaluate_release_gates import (
    REQUIRED_GATES,
    GateEvidence,
    GateStatus,
    MarketDecision,
    evaluate_release_gates,
)


def test_rc13_pre_pilot_baseline_evaluates_to_hold():
    """Verifies that in the pre-pilot state (without live founder evidence cards),

    the release gate engine evaluates to HOLD, preventing premature deployment.
    """
    current_evidence_map: dict[str, GateEvidence] = {}
    result = evaluate_release_gates(current_evidence_map)

    assert result.decision == MarketDecision.HOLD
    assert set(result.unknown) == set(REQUIRED_GATES)
    assert not result.passed
    assert not result.failed


def test_rc13_complete_founder_evidence_evaluates_to_go():
    """Verifies that once all gates G1-G6 have verified founder evidence cards,

    the release decision evaluates to GO.
    """
    founder_evidence: dict[str, GateEvidence] = {
        gate_id: GateEvidence(
            gate_id=gate_id,
            status=GateStatus.PASS,
            evidence_reference="docs/reengineering/RC13/fixtures/sample_evidence.json",
            reviewed_by="founder",
            reviewed_at="2026-11-09T12:00:00Z",
            is_synthetic=False,
        )
        for gate_id in REQUIRED_GATES
    }

    result = evaluate_release_gates(founder_evidence, verify_references_on_disk=True)
    assert result.decision == MarketDecision.GO
    assert len(result.passed) == 6
    assert not result.failed
    assert not result.unknown


def test_rc13_single_failed_gate_blocks_with_fix():
    """Verifies that if any gate fails, the engine returns FIX rather than GO or HOLD."""
    founder_evidence: dict[str, GateEvidence] = {
        gate_id: GateEvidence(
            gate_id=gate_id,
            status=GateStatus.PASS,
            evidence_reference="docs/reengineering/RC13/fixtures/sample_evidence.json",
            reviewed_by="founder",
            reviewed_at="2026-11-09T12:00:00Z",
            is_synthetic=False,
        )
        for gate_id in REQUIRED_GATES
    }
    founder_evidence["G5"] = GateEvidence(
        gate_id="G5",
        status=GateStatus.FAIL,
        evidence_reference="docs/reengineering/RC13/fixtures/sample_evidence.json",
        reviewed_by="founder",
        reviewed_at="2026-11-09T12:00:00Z",
        is_synthetic=False,
    )

    result = evaluate_release_gates(founder_evidence)
    assert result.decision == MarketDecision.FIX
    assert "G5" in result.failed
