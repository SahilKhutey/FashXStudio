"""Aggregate Staging Deployment Validation Reports.

Scans `reports/staging/` for individual validation output files:
- deployment_report.json (3.7.2)
- database_report.json (3.7.3)
- redis_report.json (3.7.4)
- storage_report.json (3.7.5)
- worker_report.json (3.7.6)
- migration_report.json (3.7.7)
- log_report.json (3.7.8)
- restart_report.json (3.7.9)
- backup_restore_report.json (3.7.10)
- rollback_report.json (3.7.11)

Outputs:
1. reports/staging/consolidated_validation_report.json
2. reports/staging/CONSOLIDATED_VALIDATION_REPORT.md
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def aggregate_reports(reports_dir: Path) -> tuple[dict[str, Any], str]:
    report_files = sorted(reports_dir.glob("*_report.json"))
    items = []
    total_passed = 0
    total_failed = 0

    for rf in report_files:
        if rf.name == "consolidated_validation_report.json":
            continue
        try:
            with open(rf, encoding="utf-8") as f:
                data = json.load(f)
            status = data.get("status", "UNKNOWN")
            if status == "PASS":
                total_passed += 1
            else:
                total_failed += 1
            items.append({
                "file": rf.name,
                "test_id": data.get("test_id", "N/A"),
                "test_name": data.get("test_name", rf.stem),
                "status": status,
                "started_at": data.get("started_at"),
                "completed_at": data.get("completed_at"),
            })
        except Exception as e:
            total_failed += 1
            items.append({
                "file": rf.name,
                "test_id": "ERR",
                "test_name": rf.stem,
                "status": "FAIL",
                "error": str(e),
            })

    overall_status = "PASS" if total_failed == 0 and len(items) > 0 else "FAIL"

    consolidated = {
        "phase": "03.7",
        "environment": "staging",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall_status,
        "summary": {
            "total_domains": len(items),
            "passed": total_passed,
            "failed": total_failed,
        },
        "results": items,
    }

    # Markdown format
    md_lines = [
        "# Consolidated Staging Validation Report",
        "",
        "**Environment:** Staging  ",
        f"**Generated:** {consolidated['generated_at']}  ",
        f"**Overall Status:** {overall_status}  ",
        "",
        "## Summary",
        "",
        f"- **Total Domains Evaluated:** {len(items)}",
        f"- **Passed:** {total_passed}",
        f"- **Failed:** {total_failed}",
        "",
        "## Validation Domain Results",
        "",
        "| Test ID | Test Name | Status | Report File |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for item in items:
        badge = "PASS" if item["status"] == "PASS" else "FAIL"
        md_lines.append(f"| {item['test_id']} | {item['test_name']} | {badge} | `{item['file']}` |")

    return consolidated, "\n".join(md_lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate Staging Validation Reports")
    parser.add_argument("--reports-dir", default="reports/staging")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    if not reports_dir.exists():
        reports_dir.mkdir(parents=True, exist_ok=True)

    consolidated_json, consolidated_md = aggregate_reports(reports_dir)

    json_file = reports_dir / "consolidated_validation_report.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(consolidated_json, f, indent=2)

    md_file = reports_dir / "CONSOLIDATED_VALIDATION_REPORT.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(consolidated_md)

    print(f"[*] Aggregated {consolidated_json['summary']['total_domains']} reports.")
    print(f"[*] Overall status: {consolidated_json['overall_status']}")
    print(f"[*] JSON report: {json_file}")
    print(f"[*] Markdown summary: {md_file}")

    return 0 if consolidated_json["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
