"""RC10 VTO reliability and provider provenance integration test."""
from __future__ import annotations

from fashx.core.rc10_timing import measure_call
from scripts.rc10.validate_metrics import is_eligible_for_pilot_claim, validate_metric_record


def test_vto_timing_measurement():
    def execute_vto_mock():
        return {"job_id": "job-rc10-1", "status": "completed", "latency_ms": 12.5}

    result, timing = measure_call(execute_vto_mock)
    assert result["job_id"] == "job-rc10-1"
    assert timing.duration_ms >= 0.0


def test_vto_metric_provenance_validation():
    # Real provider metrics pass eligibility check
    real_metric = {
        "metric_name": "vto_p95_latency_ms",
        "value": 1150.0,
        "sample_size": 100,
        "period_start": "2026-11-01T00:00:00+00:00",
        "period_end": "2026-11-05T00:00:00+00:00",
        "extracted_at": "2026-11-05T01:00:00+00:00",
        "evidence_type": "real",
        "source_reference": "vto-staging-benchmark-20261105",
    }
    assert is_eligible_for_pilot_claim(real_metric)

    # Simulated metrics are strictly rejected from pilot/beta claims
    simulated_metric = dict(real_metric, evidence_type="simulated")
    assert not is_eligible_for_pilot_claim(simulated_metric)
    errors = validate_metric_record(simulated_metric)
    assert not errors  # valid syntax/schema, but not eligible for real pilot claims
