"""RC13 Release Gates Evaluator (G1–G6 Final Market Readiness)."""
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

REQUIRED_GATES: tuple[str, ...] = ("G1", "G2", "G3", "G4", "G5", "G6")


class GateStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class MarketDecision(StrEnum):
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
    is_synthetic: bool = False


@dataclass(frozen=True)
class ReleaseGateResult:
    decision: MarketDecision
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    unknown: tuple[str, ...]
    reasons: tuple[str, ...]


def evaluate_release_gates(
    evidence_map: Mapping[str, GateEvidence],
) -> ReleaseGateResult:
    """Evaluates release gates G1-G6 against verified evidence records.

    Fail-closed:
    - Any gate failure results in FIX.
    - Any unmeasured, missing, unverified, or synthetic gate results in HOLD.
    - Only 100% verified real PASS across all six gates allows GO.
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
            if rec.is_synthetic:
                unknown.append(gate)
                reasons.append(f"gate_{gate}_synthetic_evidence_rejected")
            elif not rec.evidence_reference or not rec.reviewed_by:
                unknown.append(gate)
                reasons.append(f"gate_{gate}_missing_reviewer_or_evidence_ref")
            else:
                passed.append(gate)
        else:
            unknown.append(gate)
            reasons.append(f"gate_{gate}_unrecognized_status")

    if failed:
        decision = MarketDecision.FIX
    elif unknown:
        decision = MarketDecision.HOLD
    elif len(passed) == len(REQUIRED_GATES):
        decision = MarketDecision.GO
    else:
        decision = MarketDecision.HOLD

    return ReleaseGateResult(
        decision=decision,
        passed=tuple(passed),
        failed=tuple(failed),
        unknown=tuple(unknown),
        reasons=tuple(reasons),
    )


def load_gates_from_json(data: dict[str, dict[str, str | bool | None]]) -> dict[str, GateEvidence]:
    """Parses raw dictionary data into GateEvidence mappings."""
    evidence: dict[str, GateEvidence] = {}
    for gate_id, item in data.items():
        st_raw = str(item.get("status", "unknown")).lower()
        status = GateStatus.PASS if st_raw == "pass" else GateStatus.FAIL if st_raw == "fail" else GateStatus.UNKNOWN
        ev_ref = item.get("evidence_reference")
        evidence[gate_id] = GateEvidence(
            gate_id=gate_id,
            status=status,
            evidence_reference=str(ev_ref) if ev_ref else None,
            reviewed_by=str(item.get("reviewed_by")) if item.get("reviewed_by") else None,
            reviewed_at=str(item.get("reviewed_at")) if item.get("reviewed_at") else None,
            is_synthetic=bool(item.get("is_synthetic", False)),
        )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RC13 Final Market Release Gates")
    parser.add_argument("--input", type=Path, help="Path to gates summary JSON file")
    args = parser.parse_args()

    if args.input and args.input.exists():
        raw_data = json.loads(args.input.read_text(encoding="utf-8"))
        evidence_map = load_gates_from_json(raw_data)
    else:
        # Default empty evaluation (current baseline)
        evidence_map = {}

    result = evaluate_release_gates(evidence_map)
    print(f"RELEASE GATE DECISION: {result.decision.value.upper()}")
    print(f"Passed Gates: {list(result.passed)}")
    print(f"Failed Gates: {list(result.failed)}")
    print(f"Unknown/Holding Gates: {list(result.unknown)}")
    if result.reasons:
        print("Reasons:")
        for r in result.reasons:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
