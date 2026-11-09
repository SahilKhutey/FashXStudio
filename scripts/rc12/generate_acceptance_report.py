"""RC12 Acceptance report generator."""
from __future__ import annotations

from collections.abc import Mapping

from scripts.rc12.beta_gates import BetaGateResult, GateEvidence, evaluate_beta_gates


def generate_acceptance_report(
    *,
    branch: str = "recovery/rc12-productization-public-beta",
    base_commit: str = "516140e",
    evidence_map: Mapping[str, GateEvidence] | None = None,
    notes: str = "",
) -> str:
    """Generates an honest, un-simulated RC12 acceptance report string."""
    evidence = evidence_map or {}
    result: BetaGateResult = evaluate_beta_gates(evidence)

    lines = [
        "# RC12 Acceptance Report: Productization & Public Beta Readiness",
        "",
        f"**Branch**: `{branch}`  ",
        f"**Base Commit**: `{base_commit}`  ",
        f"**Public Beta Decision**: **{result.decision.value.upper()}**  ",
        "",
        "## 1. Public Beta Release Gates (G1–G6)",
        "",
        "| Gate | Description | Status | Evidence Reference |",
        "| :--- | :--- | :--- | :--- |",
    ]

    gate_names = {
        "G1": "Real-Stack User Journey",
        "G2": "Production Hardening & Migrations",
        "G3": "VTO Quality & SLA",
        "G4": "Privacy, Recovery & Security",
        "G5": "Catalog Rights & Legal",
        "G6": "Real User Evaluation & Pilot",
    }

    for gate in ("G1", "G2", "G3", "G4", "G5", "G6"):
        rec = evidence.get(gate)
        status_str = rec.status.value.upper() if rec else "UNKNOWN"
        ref_str = rec.evidence_reference if (rec and rec.evidence_reference) else "Pending human verification"
        lines.append(f"| `{gate}` | {gate_names.get(gate, gate)} | **{status_str}** | {ref_str} |")

    lines.extend([
        "",
        "## 2. Gate Decision Summary",
        "",
        f"- **Decision**: `{result.decision.value}`",
        f"- **Passed ({len(result.passed)})**: {', '.join(result.passed) if result.passed else 'None'}",
        f"- **Failed ({len(result.failed)})**: {', '.join(result.failed) if result.failed else 'None'}",
        f"- **Unknown / Missing ({len(result.unknown)})**: {', '.join(result.unknown) if result.unknown else 'None'}",
        "",
        "## 3. Workstream Delivery Status",
        "",
        "- **Workstream A (Release Policy)**: Implemented in `fashx.core.release_policy` with fail-closed capabilities.",
        "- **Workstream B (Catalog Operations)**: Operational health monitoring in `scripts.rc12.catalog_health`.",
        "- **Workstream C (VTO Operations)**: Cost accounting and quota monitoring in `scripts.rc12.vto_cost_report`.",
        "- **Workstream G (Launch Governance)**: Release gate evaluator in `scripts.rc12.beta_gates`.",
        "",
        "## 4. Notes & Operational Boundaries",
        "",
        notes if notes else "Public launch remains strictly held until gates G1-G6 are verified by the human founder with real-stack evidence.",
        "",
    ])

    return "\n".join(lines)
