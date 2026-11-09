"""RC11 Pilot authorization and prerelease readiness release tests."""
from __future__ import annotations

from collections.abc import Mapping

MANDATORY_PILOT_PREREQUISITES = (
    "G1_real_stack_journey",
    "G3_vto_quality_reliability",
    "G4_privacy_erasure_legal",
    "G5_catalog_vendor_rights",
    "RC08_staging_readiness",
    "RC10_beta_readiness",
    "pilot_plan_discrepancy_resolved",
    "kill_switches_tested",
    "support_incident_owner_assigned",
)


def evaluate_pilot_authorization(requirements: Mapping[str, bool]) -> tuple[str, list[str]]:
    """Evaluates pilot prerequisites. Returns ('AUTHORIZED' | 'NOT_AUTHORIZED', missing_list)."""
    missing = [req for req in MANDATORY_PILOT_PREREQUISITES if requirements.get(req) is not True]
    if missing:
        return "NOT_AUTHORIZED", missing
    return "AUTHORIZED", []


def test_missing_prerequisites_block_authorization():
    # In current state, G1-G5 are unmeasured, so authorization MUST be blocked
    current_state = {
        "RC08_staging_readiness": True,
        "RC10_beta_readiness": True,
    }
    status, missing = evaluate_pilot_authorization(current_state)
    assert status == "NOT_AUTHORIZED"
    assert "G1_real_stack_journey" in missing
    assert "G3_vto_quality_reliability" in missing
    assert "G4_privacy_erasure_legal" in missing
    assert "G5_catalog_vendor_rights" in missing


def test_all_prerequisites_grant_authorization():
    fully_cleared = dict.fromkeys(MANDATORY_PILOT_PREREQUISITES, True)
    status, missing = evaluate_pilot_authorization(fully_cleared)
    assert status == "AUTHORIZED"
    assert not missing
