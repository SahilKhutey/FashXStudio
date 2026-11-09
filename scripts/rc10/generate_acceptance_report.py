"""RC10 Acceptance report generator."""
from __future__ import annotations

from collections.abc import Mapping

from scripts.rc10.beta_gates import GateDecision, evaluate_beta_gates


def generate_acceptance_report(
    *,
    branch: str = "recovery/rc10-product-optimization",
    base_commit: str = "9e555da",
    gate_statuses: Mapping[str, bool] | None = None,
    catalog_summary: dict[str, int | float] | None = None,
    notes: str = "",
) -> str:
    """Generates an honest, un-simulated RC10 acceptance report string."""
    gates = gate_statuses or {}
    decision: GateDecision = evaluate_beta_gates(gates)

    cat = catalog_summary or {
        "total_evaluated": 0,
        "passed": 0,
        "failed": 0,
    }

    report_lines = [
        "# RC10 Acceptance Report: Product Optimization & Beta Readiness",
        "",
        f"**Branch**: `{branch}`  ",
        f"**Base Commit**: `{base_commit}`  ",
        f"**Evaluation Decision**: **{decision.decision}**  ",
        "",
        "## 1. Beta Release Gates (B1–B9)",
        "",
        "| Gate | Name | Status |",
        "| :--- | :--- | :--- |",
    ]

    for gate in (
        "B1_complete_journey",
        "B2_catalog_permissions",
        "B3_recommendation_quality",
        "B4_vto_truthfulness",
        "B5_privacy",
        "B6_reliability",
        "B7_mobile_qa",
        "B8_operations",
        "B9_legal_review",
    ):
        status_str = "PASSED" if gate in decision.passed else ("BLOCKED" if gate in decision.blocked else "UNVERIFIED")
        report_lines.append(f"| `{gate}` | {gate.replace('_', ' ').title()} | **{status_str}** |")

    report_lines.extend([
        "",
        "## 2. Gate Status Summary",
        "",
        f"- **Passed Gates ({len(decision.passed)})**: {', '.join(decision.passed) if decision.passed else 'None'}",
        f"- **Blocked Gates ({len(decision.blocked)})**: {', '.join(decision.blocked) if decision.blocked else 'None'}",
        f"- **Missing / Unverified Gates ({len(decision.missing)})**: {', '.join(decision.missing) if decision.missing else 'None'}",
        "",
        "## 3. Catalog & Recommendation Optimization Status",
        "",
        f"- Evaluated Catalog Items: `{cat.get('total_evaluated', 0)}`",
        f"- Cleared Items: `{cat.get('passed', 0)}`",
        f"- Flagged/Uncleared: `{cat.get('failed', 0)}`",
        "",
        "## 4. Notes & Operational Dependencies",
        "",
        notes if notes else "Real pilot/user evidence is tracked separately. Under AGENTS.md Rule 1 & Rule 2, only verified command outputs are recorded.",
        "",
    ])

    return "\n".join(report_lines)
