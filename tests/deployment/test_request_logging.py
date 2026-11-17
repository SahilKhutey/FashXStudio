from scripts.staging.validate_logs import validate_logging_subsystem


def test_logging_subsystem_validation():
    outcome = validate_logging_subsystem()
    assert outcome["overall"] == "PASS"
    steps = {s["step"]: s["status"] for s in outcome["steps"]}
    assert steps["json_schema_validation"] == "PASS"
    assert steps["sensitive_data_redaction"] == "PASS"
    assert steps["traceparent_propagation"] == "PASS"
