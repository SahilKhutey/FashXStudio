import json
from pathlib import Path

from scripts.staging.generate_report import aggregate_reports


def test_aggregate_reports_success(tmp_path: Path):
    r1 = {
        "phase": "03.7",
        "environment": "staging",
        "test_id": "3.7.2",
        "test_name": "health_endpoints",
        "status": "PASS",
        "started_at": "2026-11-15T00:00:00Z",
        "completed_at": "2026-11-15T00:00:01Z",
    }
    r2 = {
        "phase": "03.7",
        "environment": "staging",
        "test_id": "3.7.3",
        "test_name": "database_connectivity",
        "status": "PASS",
        "started_at": "2026-11-15T00:00:02Z",
        "completed_at": "2026-11-15T00:00:03Z",
    }
    with open(tmp_path / "deployment_report.json", "w", encoding="utf-8") as f:
        json.dump(r1, f)
    with open(tmp_path / "database_report.json", "w", encoding="utf-8") as f:
        json.dump(r2, f)

    consolidated, md = aggregate_reports(tmp_path)
    assert consolidated["overall_status"] == "PASS"
    assert consolidated["summary"]["total_domains"] == 2
    assert consolidated["summary"]["passed"] == 2
    assert consolidated["summary"]["failed"] == 0
    assert "3.7.2" in md
    assert "3.7.3" in md


def test_aggregate_reports_with_failure(tmp_path: Path):
    r1 = {
        "phase": "03.7",
        "environment": "staging",
        "test_id": "3.7.2",
        "test_name": "health_endpoints",
        "status": "FAIL",
    }
    with open(tmp_path / "deployment_report.json", "w", encoding="utf-8") as f:
        json.dump(r1, f)

    consolidated, _ = aggregate_reports(tmp_path)
    assert consolidated["overall_status"] == "FAIL"
    assert consolidated["summary"]["failed"] == 1
