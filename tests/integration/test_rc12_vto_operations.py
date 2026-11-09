from scripts.rc12.vto_cost_report import compile_vto_cost_report


def test_vto_cost_report_compiles_mock_and_real():
    jobs = [
        {"job_id": "j1", "mode": "real", "cost_usd": 0.05, "duration_ms": 12000, "status": "completed"},
        {"job_id": "j2", "mode": "real", "cost_usd": 0.05, "duration_ms": 15000, "status": "completed"},
        {"job_id": "j3", "mode": "mock", "cost_usd": None, "duration_ms": 200, "status": "completed"},
        {"job_id": "j4", "mode": "real", "cost_usd": 0.05, "duration_ms": 40000, "status": "failed"},
    ]

    report = compile_vto_cost_report(jobs, budget_usd=1.0)
    assert report.total_jobs == 4
    assert report.real_jobs == 3
    assert report.mock_jobs == 1
    assert report.failed_jobs == 1
    assert report.total_spend_usd == 0.15
    assert report.budget_used_percent == 15.0
    assert not report.spend_warning_triggered
    assert report.p95_latency_ms is not None


def test_vto_cost_report_triggers_budget_warning():
    jobs = [
        {"job_id": f"j-{i}", "mode": "real", "cost_usd": 10.0, "duration_ms": 10000}
        for i in range(29)  # 29 * $10 = $290 > 80% of $350 ($280)
    ]
    report = compile_vto_cost_report(jobs, budget_usd=350.0)
    assert report.total_spend_usd == 290.0
    assert report.spend_warning_triggered is True
