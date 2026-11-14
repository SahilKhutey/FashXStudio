from scripts.rc13.evaluate_vto import (
    VTODecision,
    evaluate_vto_jobs,
)


def sample_job(job_id: str = "job-001", **kwargs: object) -> dict[str, object]:
    job: dict[str, object] = {
        "job_id": job_id,
        "provider": "fashx_gpu_vendor_a",
        "status": "completed",
        "latency_seconds": 12.5,
        "rating": 4.5,
        "artifacts_detected": False,
        "body_distortion": False,
        "garment_mismatch": False,
        "identity_drift": False,
        "blur_defect": False,
        "is_synthetic": False,
    }
    job.update(kwargs)
    return job


def test_valid_real_vto_jobs_pass_gate_and_targets():
    jobs = [sample_job(f"job-{i}", latency_seconds=10.0 + i) for i in range(20)]
    res = evaluate_vto_jobs(jobs, require_real_provider=True)
    assert res.decision == VTODecision.PASS
    assert res.meets_operational_targets is True
    assert res.total_jobs == 20
    assert res.completed_jobs == 20
    assert res.defective_jobs_count == 0
    assert res.completion_rate == 1.0
    assert res.defect_job_rate == 0.0
    assert "completion_rate" in res.passed_gate_checks
    assert "defect_rate" in res.passed_gate_checks
    assert "p95_latency" in res.passed_gate_checks
    assert "mean_rating" in res.passed_gate_checks


def test_passes_gate_ceiling_but_misses_stricter_target():
    # 35s latency: passes gate ceiling (<=45s) but misses target (<=30s)
    jobs = [sample_job(f"job-{i}", latency_seconds=35.0) for i in range(10)]
    res = evaluate_vto_jobs(jobs, require_real_provider=True)
    assert res.decision == VTODecision.PASS  # Gate passes!
    assert res.meets_operational_targets is False  # Target misses!
    assert "p95_latency" in res.passed_gate_checks
    assert "p95_latency" not in res.passed_operational_targets


def test_mock_provider_rejected_when_real_required():
    jobs = [sample_job("job-mock", provider="mock")]
    res = evaluate_vto_jobs(jobs, require_real_provider=True)
    assert res.decision == VTODecision.HOLD
    assert any("mock_or_synthetic_provider_detected" in r for r in res.reasons)

    # Allowed when require_real_provider is False
    res_mock_allowed = evaluate_vto_jobs(jobs, require_real_provider=False)
    assert res_mock_allowed.decision == VTODecision.PASS


def test_defect_deduplication():
    # 10 completed jobs, 1 job has MULTIPLE defect tags
    jobs = [sample_job(f"job-{i}") for i in range(9)]
    multi_defect_job = sample_job(
        "job-multi",
        artifacts_detected=True,
        body_distortion=True,
        garment_mismatch=True,
    )
    jobs.append(multi_defect_job)

    res = evaluate_vto_jobs(jobs, require_real_provider=True)
    # The count of defective jobs MUST be 1, not 3!
    assert res.defective_jobs_count == 1
    assert res.defect_job_rate == 0.10  # 1/10 = 10% <= 15% gate ceiling
    assert res.decision == VTODecision.PASS


def test_completion_rate_below_gate_ceiling_fails():
    jobs = [
        sample_job("job-1", status="completed"),
        sample_job("job-2", status="failed"),
    ]  # 50% completion rate < 90% min gate
    res = evaluate_vto_jobs(jobs, require_real_provider=True)
    assert res.decision == VTODecision.FAIL
    assert "completion_rate" in res.failed_gate_checks


def test_latency_above_gate_ceiling_fails():
    # Latency 50.0s > 45.0s gate ceiling
    jobs = [sample_job(f"job-{i}", latency_seconds=50.0) for i in range(10)]
    res = evaluate_vto_jobs(jobs, require_real_provider=True)
    assert res.decision == VTODecision.FAIL
    assert "p95_latency" in res.failed_gate_checks


def test_empty_jobs_holds():
    res = evaluate_vto_jobs([], require_real_provider=True)
    assert res.decision == VTODecision.HOLD
    assert "empty_vto_job_list" in res.reasons
