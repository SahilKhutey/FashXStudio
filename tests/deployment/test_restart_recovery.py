from scripts.staging.validate_restart import validate_restart_configuration


def test_restart_recovery_validation():
    outcome = validate_restart_configuration()
    assert outcome["overall"] == "PASS"
    steps = {s["step"]: s["status"] for s in outcome["steps"]}
    assert steps["worker_acknowledgement_policy"] == "PASS"
