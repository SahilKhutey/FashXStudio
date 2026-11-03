from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def audit_database(root: Path) -> dict[str, Any]:
    migrations_dir = root / "database" / "migrations" / "versions"
    models_dir = root / "database" / "models"

    migration_files = (
        sorted([f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"])
        if migrations_dir.exists()
        else []
    )
    model_files = (
        sorted([f for f in models_dir.glob("*.py") if f.name != "__init__.py"])
        if models_dir.exists()
        else []
    )

    revisions = []
    heads = set()
    down_revisions = set()

    for path in migration_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        revision = None
        down_revision = None

        rev_match = re.search(
            r"^revision(?:\s*:\s*[^=\n]+)?\s*=\s*['\"]([^'\"]+)['\"]",
            content,
            re.MULTILINE,
        )
        if rev_match:
            revision = rev_match.group(1).strip()

        down_match = re.search(
            r"^down_revision(?:\s*:\s*[^=\n]+)?\s*=\s*['\"]?([^'\"\n]+)['\"]?",
            content,
            re.MULTILINE,
        )
        if down_match:
            raw_down = down_match.group(1).strip()
            if raw_down != "None":
                down_revision = raw_down

        if revision:
            revisions.append({
                "file": path.name,
                "revision": revision,
                "down_revision": down_revision,
            })
            heads.add(revision)
            if down_revision:
                down_revisions.add(down_revision)

    actual_heads = list(heads - down_revisions)

    findings: list[dict[str, Any]] = []
    if len(actual_heads) > 1:
        findings.append({
            "id": "DB-MULTIPLE-HEADS",
            "severity": "P0",
            "subsystem": "database",
            "status": "CONFIRMED",
            "title": f"Multiple Alembic migration heads detected: {actual_heads}",
            "evidence": "database/migrations/versions",
            "recommendation": "Merge heads using alembic merge.",
        })

    return {
        "status": "success" if not findings else "warning",
        "migration_count": len(revisions),
        "revisions": revisions,
        "heads": actual_heads,
        "model_file_count": len(model_files),
        "models": [f.name for f in model_files],
        "findings": findings,
    }
