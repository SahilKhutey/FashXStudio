"""RC12 Public Beta Release Gate Evaluator."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

REQUIRED_GATES = ("G1", "G2", "G3", "G4", "G5", "G6")


class GateStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class BetaDecision(StrEnum):
    GO = "go"
    FIX = "fix"
    HOLD = "hold"


@dataclass(frozen=True)
class GateEvidence:
    gate_id: str
    status: GateStatus
    evidence_reference: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None


@dataclass(frozen=True)
class BetaGateResult:
    decision: BetaDecision
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    unknown: tuple[str, ...]
    reasons: tuple[str, ...]


def evaluate_beta_gates(
    evidence_map: Mapping[str, GateEvidence],
) -> BetaGateResult:
    """Evaluates release gates G1-G6 against verified evidence records.

    Fail-closed: All gates must be verified PASS with documented reviewer and evidence reference.
    """
    passed: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []
    reasons: list[str] = []

    for gate in REQUIRED_GATES:
        rec = evidence_map.get(gate)
        if rec is None or rec.status == GateStatus.UNKNOWN:
            unknown.append(gate)
            reasons.append(f"gate_{gate}_unmeasured_or_missing")
        elif rec.status == GateStatus.FAIL:
            failed.append(gate)
            reasons.append(f"gate_{gate}_failed")
        elif rec.status == GateStatus.PASS:
            if not rec.evidence_reference or not rec.reviewed_by:
                unknown.append(gate)
                reasons.append(f"gate_{gate}_missing_reviewer_or_evidence_ref")
            else:
                passed.append(gate)

    if failed:
        decision = BetaDecision.FIX
    elif unknown:
        decision = BetaDecision.HOLD
    elif len(passed) == len(REQUIRED_GATES):
        decision = BetaDecision.GO
    else:
        decision = BetaDecision.HOLD

    return BetaGateResult(
        decision=decision,
        passed=tuple(passed),
        failed=tuple(failed),
        unknown=tuple(unknown),
        reasons=tuple(reasons),
    )
