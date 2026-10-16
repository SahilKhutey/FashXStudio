"""Export backend ErrorCode enum to mobile/src/api/error-codes.json."""

from __future__ import annotations

import json
from pathlib import Path

from fashx.core.errors import ErrorCode


def export_error_codes(output_path: Path | None = None) -> dict[str, str]:
    if output_path is None:
        output_path = Path("mobile/src/api/error-codes.json")

    codes = {e.name: e.value for e in ErrorCode}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(codes, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return codes


if __name__ == "__main__":
    out = Path("mobile/src/api/error-codes.json")
    exported = export_error_codes(out)
    print(f"Exported {len(exported)} error codes to {out}")
