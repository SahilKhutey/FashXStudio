from unittest.mock import MagicMock

from scripts.staging.validate_redis import validate_redis_operations


def test_redis_operations_success():
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.get.side_effect = [b"validation-ok", None]
    mock_client.llen.return_value = 0

    outcome = validate_redis_operations(mock_client)
    assert outcome["overall"] == "PASS"
    steps = {s["step"]: s["status"] for s in outcome["steps"]}
    assert steps["ping"] == "PASS"
    assert steps["ephemeral_round_trip"] == "PASS"
    assert steps["queue_inspection"] == "PASS"


def test_redis_operations_ping_failure():
    mock_client = MagicMock()
    mock_client.ping.side_effect = ConnectionError("Connection refused")

    outcome = validate_redis_operations(mock_client)
    assert outcome["overall"] == "FAIL"
    assert outcome["steps"][0]["step"] == "ping"
    assert outcome["steps"][0]["status"] == "FAIL"
