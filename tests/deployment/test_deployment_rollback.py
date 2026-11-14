from scripts.staging.validate_rollback import validate_rollback_readiness


def test_deployment_rollback_readiness():
    outcome = validate_rollback_readiness()
    assert outcome["overall"] == "PASS"
    steps = {s["step"]: s["status"] for s in outcome["steps"]}
    assert steps["rollback_script_exists"] == "PASS"
    assert steps["state_capture_schema"] == "PASS"
    assert steps["database_rollback_policy"] == "PASS"
