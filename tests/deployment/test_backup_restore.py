from scripts.staging.validate_backup_restore import validate_backup_restore_policy


def test_backup_restore_policy():
    outcome = validate_backup_restore_policy()
    assert outcome["overall"] == "PASS"
    steps = {s["step"]: s["status"] for s in outcome["steps"]}
    assert steps["backup_parameters"] == "PASS"
    assert steps["dr_object_storage_coupling"] == "PASS"
