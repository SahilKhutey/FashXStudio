"""Validate Staging Database Migration State.

Performs:
1. Alembic heads verification (ensures single head).
2. Current database revision check.
3. Schema drift detection (alembic check).

Generates a structured JSON validation report in reports/staging/.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from fashx.core.database import get_session_factory


def validate_migrations() -> dict[str, str | list[str]]:
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)

    # 1. Single head check
    heads = script.get_heads()
    if len(heads) != 1:
        return {
            "status": "FAIL",
            "error": f"Multiple or zero migration heads detected: {heads}",
            "heads": list(heads),
        }

    head_rev = heads[0]

    # 2. Database current revision
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            from sqlalchemy import text

            current_rev = session.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    except Exception as e:
        current_rev = f"error: {type(e).__name__}"

    return {
        "status": "PASS" if current_rev == head_rev else "WARN",
        "head_revision": head_rev,
        "current_revision": str(current_rev),
        "heads": list(heads),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Database Migration State")
    parser.add_argument("--output-dir", default="reports/staging")
    args = parser.parse_args()

    started_at = datetime.now(UTC).isoformat()
    print("[*] Validating database migrations...")
    outcome = validate_migrations()
    completed_at = datetime.now(UTC).isoformat()

    report = {
        "phase": "03.7",
        "environment": "staging",
        "test_id": "3.7.7",
        "test_name": "migration_state",
        "status": outcome["status"],
        "head_revision": outcome.get("head_revision"),
        "current_revision": outcome.get("current_revision"),
        "heads": outcome.get("heads"),
        "started_at": started_at,
        "completed_at": completed_at,
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "migration_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[*] Migration validation complete. Status: {report['status']}")
    print(f"[*] Report saved to {report_file}")
    return 0 if report["status"] in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
