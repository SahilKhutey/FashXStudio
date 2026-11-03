from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from audit.rc00.api_audit import audit_api
from audit.rc00.backend_audit import audit_backend
from audit.rc00.database_audit import audit_database
from audit.rc00.github_audit import audit_github
from audit.rc00.inventory import scan_repository
from audit.rc00.mobile_audit import audit_mobile
from audit.rc00.report import write_report
from audit.rc00.runtime_audit import audit_runtime
from audit.rc00.test_audit import audit_tests


def run_audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    print(f"[*] Scanning repository from root: {root}")

    inventory_data = scan_repository(root)
    print(f"    - Found {inventory_data['file_count']} source/config files")

    backend_data = audit_backend(root)
    print(f"    - Verified {backend_data['module_count']}/{backend_data['expected_module_count']} backend modules")

    mobile_data = audit_mobile(root)
    print(f"    - Mobile package status: {mobile_data['status']} (Screens: {mobile_data['screen_count']})")

    database_data = audit_database(root)
    print(f"    - Database migrations: {database_data['migration_count']} revisions (Heads: {database_data['heads']})")

    runtime_data = audit_runtime(root)
    print(f"    - Runtime checks completed (Risks identified: {len(runtime_data['findings'])})")

    tests_data = audit_tests(root)
    print(f"    - Tests discovered: {tests_data['test_file_count']} files")

    github_data = audit_github(root)
    print(f"    - Git branch: {github_data.get('branch')} @ {github_data.get('head', '')[:7]}")

    api_data = audit_api()
    print(f"    - API route extraction: {api_data.get('route_count')} endpoints")

    data: dict[str, Any] = {
        "project": {
            "name": "FashXStudio",
            "repository": "SahilKhutey/FashXStudio",
            "audit": "RC-00",
        },
        "inventory": inventory_data,
        "backend": backend_data,
        "mobile": mobile_data,
        "database": database_data,
        "runtime": runtime_data,
        "tests": tests_data,
        "github": github_data,
        "api": api_data,
    }

    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FashXStudio RC-00 Technical Audit")
    parser.add_argument("--root", type=str, default=".", help="Repository root path")
    parser.add_argument("--output", type=str, default="audit/reports/rc00", help="Output directory for reports")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output_dir = Path(args.output).resolve()

    data = run_audit(root)
    report_path = write_report(data, output_dir)
    print(f"[OK] RC-00 audit complete. Report written to: {report_path}")


if __name__ == "__main__":
    main()
