from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    # 1. Runtime findings
    runtime = data.get("runtime", {})
    for f in runtime.get("findings", []):
        findings.append(f)

    # 2. Backend findings
    backend = data.get("backend", {})
    for f in backend.get("findings", []):
        findings.append(f)

    # 3. Mobile findings
    mobile = data.get("mobile", {})
    for f in mobile.get("findings", []):
        findings.append(f)

    # 4. Database findings
    db = data.get("database", {})
    for f in db.get("findings", []):
        findings.append(f)

    # 5. Core domain breaking points from verified investigation
    findings.extend([
        {
            "id": "FX-001",
            "severity": "P0",
            "subsystem": "catalog",
            "status": "CONFIRMED",
            "title": "Catalog is unpopulated and feed has no product candidates",
            "evidence": "fashx_local.db has 0 canonical_garments and 0 merchant_products",
            "root_cause": "scripts/catalog/seed_local.py halted because 'own-wardrobe' source was unregistered",
            "recommendation": "Register and clear 'own-wardrobe' source and run seed_local.py --apply",
        },
        {
            "id": "FX-003",
            "severity": "P0",
            "subsystem": "wardrobe",
            "status": "CONFIRMED",
            "title": "Closet collection is completely empty in local database",
            "evidence": "fashx_local.db wardrobe_items row count is 0",
            "root_cause": "No wardrobe save events occurred due to empty catalog items in feed",
            "recommendation": "Populate catalog and verify end-to-end save-to-closet flow",
        },
        {
            "id": "FX-004",
            "severity": "P0",
            "subsystem": "tryon",
            "status": "CONFIRMED",
            "title": "VTO async dispatch stalls in non-Celery development environments",
            "evidence": "backend/fashx/tryon/ports_dispatch.py logs warning and defers dispatch silently",
            "root_cause": "CeleryTryOnJobDispatcher has no in-process or async background worker fallback",
            "recommendation": "Add in-process / async fallback dispatcher for local dev environments",
        },
        {
            "id": "FX-009",
            "severity": "P1",
            "subsystem": "mobile",
            "status": "CONFIRMED",
            "title": "Settings screen exposes internal database UUIDs to consumers",
            "evidence": "mobile/app/settings/index.tsx displays raw userId and photo.id",
            "root_cause": "Diagnostic identifiers were rendered in consumer settings card without styling abstraction",
            "recommendation": "Redesign settings into consumer account profile and privacy controls",
        },
    ])

    return findings


def write_report(data: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    findings = build_findings(data)
    now_iso = datetime.now(UTC).isoformat()

    findings_payload = {
        "generated_at": now_iso,
        "audit": "RC-00",
        "findings": findings,
    }

    # Write findings.json
    findings_file = output_dir / "findings.json"
    findings_file.write_text(json.dumps(findings_payload, indent=2), encoding="utf-8")

    # Write baseline.json
    baseline_file = output_dir / "baseline.json"
    baseline_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Generate RC00_FINAL_REPORT.md
    md_lines = [
        "# FashXStudio — RC-00 Final Audit Report",
        "",
        f"**Generated at**: {now_iso}  ",
        "**Audit Status**: COMPLETED  ",
        f"**Git Branch**: `{data.get('github', {}).get('branch', 'unknown')}`  ",
        f"**HEAD Commit**: `{data.get('github', {}).get('head', 'unknown')}`  ",
        "",
        "---",
        "",
        "## 1. Inventory Summary",
        "",
        f"- **Total Tracked Files**: {data.get('inventory', {}).get('file_count', 0)}",
        f"- **Backend Modules**: {data.get('backend', {}).get('module_count', 0)} of {data.get('backend', {}).get('expected_module_count', 0)} expected",
        f"- **Mobile Screens**: {data.get('mobile', {}).get('screen_count', 0)} in `mobile/app/`",
        f"- **Database Migrations**: {data.get('database', {}).get('migration_count', 0)} applied revisions",
        f"- **Alembic Heads**: `{data.get('database', {}).get('heads', [])}`",
        f"- **Test Files**: {data.get('tests', {}).get('test_file_count', 0)} ({data.get('tests', {}).get('backend_test_file_count', 0)} backend, {data.get('tests', {}).get('mobile_test_file_count', 0)} mobile)",
        f"- **OpenAPI Endpoints**: {data.get('api', {}).get('openapi_endpoint_count', data.get('api', {}).get('route_count', 0))}",
        "",
        "---",
        "",
        "## 2. Findings Register",
        "",
        "| ID | Severity | Status | Subsystem | Title | Evidence |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for f in findings:
        md_lines.append(
            f"| `{f['id']}` | **{f['severity']}** | `{f['status']}` | `{f['subsystem']}` | {f['title']} | `{f.get('evidence', '')}` |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## 3. Transition to RC-01",
        "",
        "The repository technical baseline is verified and documented.",
        "Proceed to **RC-01: Backend Functionality Recovery** (Data hydration, catalog source registration, and in-process VTO execution).",
    ])

    report_file = output_dir / "RC00_FINAL_REPORT.md"
    report_file.write_text("\n".join(md_lines), encoding="utf-8")

    return report_file
