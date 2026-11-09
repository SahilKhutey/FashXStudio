from scripts.rc10.validate_metrics import (
    is_eligible_for_pilot_claim,
    validate_metric_record,
)


def valid_record():
    return {
        "metric_name": "vto_completion_rate",
        "value": 0.82,
        "sample_size": 40,
        "period_start": "2026-11-01T00:00:00+00:00",
        "period_end": "2026-11-04T23:59:59+00:00",
        "extracted_at": "2026-11-05T05:00:00+00:00",
        "evidence_type": "real",
        "source_reference": "approved-report-export-001",
    }


def test_valid_real_metric_is_eligible():
    assert is_eligible_for_pilot_claim(valid_record())


def test_simulated_metric_is_not_eligible():
    record = valid_record()
    record["evidence_type"] = "simulated"
    assert not is_eligible_for_pilot_claim(record)


def test_empty_sample_is_not_eligible():
    record = valid_record()
    record["sample_size"] = 0
    assert not is_eligible_for_pilot_claim(record)


def test_missing_fields_fail_validation():
    record = valid_record()
    del record["metric_name"]
    errors = validate_metric_record(record)
    assert "missing_metric_name" in errors


def test_invalid_evidence_type_fails():
    record = valid_record()
    record["evidence_type"] = "unsupported_fabrication"
    errors = validate_metric_record(record)
    assert "invalid_evidence_type" in errors
