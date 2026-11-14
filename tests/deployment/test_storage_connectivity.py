from unittest.mock import MagicMock

from scripts.staging.validate_storage import validate_storage_operations


def test_storage_operations_round_trip():
    mock_storage = MagicMock()
    mock_storage.get.side_effect = [b"fashx-staging-validation-payload", None]

    outcome = validate_storage_operations(mock_storage)
    assert outcome["overall"] == "PASS"
    steps = {s["step"]: s["status"] for s in outcome["steps"]}
    assert steps["upload"] == "PASS"
    assert steps["download_and_verify"] == "PASS"
    assert steps["delete"] == "PASS"
    assert steps["confirm_deleted"] == "PASS"


def test_storage_operations_upload_failure():
    mock_storage = MagicMock()
    mock_storage.put.side_effect = RuntimeError("S3 AccessDenied")

    outcome = validate_storage_operations(mock_storage)
    assert outcome["overall"] == "FAIL"
    assert outcome["steps"][0]["step"] == "upload"
    assert outcome["steps"][0]["status"] == "FAIL"
