#!/usr/bin/env python3
"""Export PhotoRejectReason values to mobile/src/api/reject-reasons.json."""

from __future__ import annotations

import json
from pathlib import Path

from schemas.common.enums import PhotoRejectReason


def get_reject_reasons() -> list[str]:
    return sorted(r.value for r in PhotoRejectReason)


def export_reject_reasons(target_path: Path | None = None) -> Path:
    if target_path is None:
        target_path = Path("mobile/src/api/reject-reasons.json")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    reasons = get_reject_reasons()
    target_path.write_text(json.dumps(reasons, indent=2) + "\n", encoding="utf-8")
    return target_path


def main() -> None:
    path = export_reject_reasons()
    print(f"Exported {len(get_reject_reasons())} reject reasons to {path}")


if __name__ == "__main__":
    main()
