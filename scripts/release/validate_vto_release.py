#!/usr/bin/env python3
"""CLI utility to validate FashXStudio Virtual Try-On release evidence.

Inspects machine-readable evidence manifest against the 6 mandatory release gates.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fashx.release.validator import (
    GATES,
    valid_number,
    validate_gate,
    validate_release,
)

__all__ = ["GATES", "valid_number", "validate_gate", "validate_release"]


def find_default_manifest(root: Path) -> Path:
    # Priority 1: Human founder empirical evidence card in docs/evidence/
    evidence_path = root / "docs" / "evidence" / "vto-release-evidence.json"
    if evidence_path.exists():
        return evidence_path
    # Priority 2: Release baseline manifest template in docs/release/
    return root / "docs" / "release" / "vto-release-evidence.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate FashXStudio VTO MVP release evidence manifest."
    )
    parser.add_argument(
        "--manifest",
        "-m",
        type=Path,
        default=None,
        help="Path to vto-release-evidence.json manifest.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        default=False,
        help="Verify that referenced evidence markdown cards exist on disk.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = args.manifest or find_default_manifest(repo_root)

    print(f"[*] Validating VTO release evidence manifest: {manifest_path}")

    if not manifest_path.exists():
        print(f"[FAIL] Manifest file not found: {manifest_path}")
        return 1

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[FAIL] Failed to parse manifest JSON: {e}")
        return 1

    base_dir = repo_root if args.check_files else None
    errors = validate_release(manifest, base_dir=base_dir)

    if errors:
        print("\n[BLOCKED] Release gate validation failed:")
        for err in errors:
            print(f"  - {err}")
        print("\nRelease status: NOT CLEARED (evidence missing or unmeasured)")
        return 1

    print("\n[RELEASE CLEARED] All 6 mandatory release gates passed with verified evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
