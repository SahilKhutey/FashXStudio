"""RC13 Release Gates Evaluator (G1–G6 Final Market Readiness).

Reconciled with repository merged baseline and authentic evidence verification.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

REQUIRED_GATES: tuple[str, ...] = ("G1", "G2", "G3", "G4", "G5", "G6")

DISALLOWED_REVIEWERS: frozenset[str] = frozenset(
    {"", "unassigned", "test", "tester", "dummy", "unknown", "nobody", "placeholder"}
)


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
    verify_references_on_disk: bool = False,
    authenticate_evidence: bool = False,
    authorized_dir: str | Path | None = None,
) -> ReleaseGateResult:
    """Evaluates release gates G1-G6 against verified evidence records.

    Fail-closed:
    - Any gate failure results in FIX.
    - Any unmeasured, missing, placeholder, or synthetic gate results in HOLD.
    - If verify_references_on_disk=True, checks that referenced evidence file exists on disk.
    - If authenticate_evidence=True:
        1. Validates that evidence file is stored inside authorized_dir (default: docs/evidence/).
        2. Validates non-placeholder reviewer and valid, non-future reviewed_at timestamp.
        3. Authenticates file checksums (SHA-256) and rejects synthetic fixtures via validate_evidence.
        4. Validates that the evidence file contains a record matching the target gate.
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
            reviewer = str(rec.reviewed_by or "").strip().lower()
            if rec.is_synthetic:
                unknown.append(gate)
                reasons.append(f"gate_{gate}_synthetic_evidence_rejected")
            elif not rec.evidence_reference or reviewer in DISALLOWED_REVIEWERS:
                unknown.append(gate)
                reasons.append(f"gate_{gate}_missing_or_placeholder_reviewer_or_ref")
            elif (verify_references_on_disk or authenticate_evidence) and not Path(rec.evidence_reference).exists():
                unknown.append(gate)
                reasons.append(f"gate_{gate}_evidence_file_not_found:{rec.evidence_reference}")
            elif authenticate_evidence:
                ref_path = Path(rec.evidence_reference)
                target_auth_dir = Path(authorized_dir or "docs/evidence")
                try:
                    resolved_ref = ref_path.resolve()
                    resolved_auth = target_auth_dir.resolve()
                    if not (resolved_ref == resolved_auth or resolved_auth in resolved_ref.parents):
                        unknown.append(gate)
                        reasons.append(f"gate_{gate}_evidence_path_unauthorized:{rec.evidence_reference}")
                        continue
                except Exception:
                    unknown.append(gate)
                    reasons.append(f"gate_{gate}_evidence_path_unauthorized:{rec.evidence_reference}")
                    continue

                if not rec.reviewed_at:
                    unknown.append(gate)
                    reasons.append(f"gate_{gate}_missing_reviewed_at")
                    continue

                try:
                    dt = datetime.fromisoformat(str(rec.reviewed_at))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                    if dt > datetime.now(UTC):
                        unknown.append(gate)
                        reasons.append(f"gate_{gate}_future_reviewed_at:{rec.reviewed_at}")
                        continue
                except Exception:
                    unknown.append(gate)
                    reasons.append(f"gate_{gate}_invalid_reviewed_at:{rec.reviewed_at}")
                    continue

                from scripts.rc13.validate_evidence import validate_evidence_file
                is_valid, errs = validate_evidence_file(
                    ref_path, disallow_synthetic=True, verify_source_files=True
                )
                if not is_valid:
                    unknown.append(gate)
                    reasons.append(f"gate_{gate}_evidence_authentication_failed:{';'.join(errs)}")
                    continue

                try:
                    content = json.loads(ref_path.read_text(encoding="utf-8"))
                    records = content if isinstance(content, list) else [content]
                    matching = [
                        r
                        for r in records
                        if r.get("gate_id") == gate
                        or (r.get("evidence_id") and gate in str(r.get("evidence_id")))
                        or r.get("type") == gate
                    ]
                    if not matching:
                        unknown.append(gate)
                        reasons.append(f"gate_{gate}_evidence_record_gate_mismatch")
                        continue
                    if any(r.get("is_synthetic", False) for r in matching):
                        unknown.append(gate)
                        reasons.append(f"gate_{gate}_synthetic_record_in_evidence_file")
                        continue
                except Exception as exc:
                    unknown.append(gate)
                    reasons.append(f"gate_{gate}_evidence_parse_error:{exc}")
                    continue

                passed.append(gate)
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
    parser.add_argument(
        "--verify-on-disk", action="store_true", help="Verify that evidence reference files exist on disk"
    )
    parser.add_argument(
        "--authenticate-evidence",
        action="store_true",
        help="Cryptographically authenticate evidence records and verify docs/evidence/ quarantine",
    )
    parser.add_argument(
        "--authorized-dir",
        type=Path,
        default=Path("docs/evidence"),
        help="Authorized evidence directory path",
    )
    args = parser.parse_args()

    if args.input and args.input.exists():
        raw_data = json.loads(args.input.read_text(encoding="utf-8"))
        evidence_map = load_gates_from_json(raw_data)
    else:
        evidence_map = {}

    result = evaluate_release_gates(
        evidence_map,
        verify_references_on_disk=args.verify_on_disk,
        authenticate_evidence=args.authenticate_evidence,
        authorized_dir=args.authorized_dir,
    )
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
