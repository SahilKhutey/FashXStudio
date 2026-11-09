"""RC10 Beta release gate evaluator."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

REQUIRED_GATES = (
    "B1_complete_journey",
    "B2_catalog_permissions",
    "B3_recommendation_quality",
    "B4_vto_truthfulness",
    "B5_privacy",
    "B6_reliability",
    "B7_mobile_qa",
    "B8_operations",
    "B9_legal_review",
)


@dataclass(frozen=True)
class GateDecision:
    decision: str
    passed: tuple[str, ...]
    blocked: tuple[str, ...]
    missing: tuple[str, ...]


def evaluate_beta_gates(gates: Mapping[str, bool]) -> GateDecision:
    """Evaluates the status of all 9 required beta gates.

    Strictly fail-closed: All gates must evaluate to True for a GO decision.
    Any gate evaluate to False blocks the release with a HOLD decision.
    Any missing/unmeasured gate blocks the release with a HOLD decision.
    """
    passed = tuple(gate for gate in REQUIRED_GATES if gates.get(gate) is True)
    blocked = tuple(gate for gate in REQUIRED_GATES if gates.get(gate) is False)
    missing = tuple(gate for gate in REQUIRED_GATES if gate not in gates)

    if len(passed) == len(REQUIRED_GATES):
        decision = "GO"
    else:
        decision = "HOLD"

    return GateDecision(
        decision=decision,
        passed=passed,
        blocked=blocked,
        missing=missing,
    )
