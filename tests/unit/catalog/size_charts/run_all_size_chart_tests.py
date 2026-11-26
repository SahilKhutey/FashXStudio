"""Consolidated Master Test Runner for Phase 08.1 Product Size Data & Revisions.

Runs all 10 unit and domain test suites for Workstream 8.1.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
backend_path = ROOT / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Environment safeguards
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"


def load_module_from_file(file_path: Path, mod_name: str):
    spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_test_module(mod, module_label: str) -> tuple[int, int]:
    passed = 0
    failed = 0
    print("\n=======================================================")
    print(f"RUNNING: {module_label}")
    print("=======================================================")
    for attr_name in dir(mod):
        if attr_name.startswith("test_"):
            fn = getattr(mod, attr_name)
            if callable(fn):
                try:
                    fn()
                    passed += 1
                    print(f"  [PASS] {attr_name}")
                except Exception as exc:
                    failed += 1
                    print(f"  [FAIL] {attr_name}: {exc}")
                    traceback.print_exc()
    return passed, failed


def main():
    start_time = time.time()
    this_dir = Path(__file__).parent

    test_files = [
        ("test_schemas.py", "Phase 08.1 - Size Chart Schemas (SZ-SCH-001 - 004)"),
        ("test_size_systems.py", "Phase 08.1 - Sizing System Registry (SZ-SYS-001 - 003)"),
        ("test_measurement_fields.py", "Phase 08.1 - Measurement Fields (SZ-FLD-001 - 002)"),
        ("test_units.py", "Phase 08.1 - Unit Normalization (SZ-UNT-001 - 003)"),
        ("test_validation.py", "Phase 08.1 - Validation Service (SZ-VAL-001 - 004)"),
        ("test_fingerprint.py", "Phase 08.1 - Canonical Fingerprint (SZ-FPT-001 - 002)"),
        ("test_freshness.py", "Phase 08.1 - Freshness Policy (SZ-FRE-001 - 004)"),
        ("test_availability.py", "Phase 08.1 - Variant Availability (SZ-AVL-001)"),
        ("test_repository_and_service.py", "Phase 08.1 - Repository & Service (SZ-REP / SRV)"),
        ("test_api_and_backward_compatibility.py", "Phase 08.1 - API & Backward Compatibility (SZ-API / E2E)"),
    ]

    total_passed = 0
    total_failed = 0

    print("=======================================================")
    print("FASHXSTUDIO PHASE 08.1 MASTER SIZE DATA TEST RUNNER")
    print("=======================================================")

    for fname, label in test_files:
        fpath = this_dir / fname
        if not fpath.exists():
            print(f"[MISSING] {fname}")
            total_failed += 1
            continue
        mod_name = f"tests.unit.catalog.size_charts.{fname.replace('.py', '')}"
        try:
            mod = load_module_from_file(fpath, mod_name)
            p, f = run_test_module(mod, label)
            total_passed += p
            total_failed += f
        except Exception as exc:
            print(f"[LOAD ERROR] {fname}: {exc}")
            traceback.print_exc()
            total_failed += 1

    elapsed = time.time() - start_time
    print("\n=======================================================")
    print("PHASE 08.1 SIZE DATA TEST RESULTS SUMMARY")
    print("=======================================================")
    print(f"Total Tests Run: {total_passed + total_failed}")
    print(f"Passed:          {total_passed}")
    print(f"Failed:          {total_failed}")
    print(f"Elapsed Time:    {elapsed:.2f}s")
    print("=======================================================")

    if total_failed == 0 and total_passed > 0:
        print("\nOVERALL VERDICT: ALL TESTS PASSED (100% GREEN)")
        return 0
    else:
        print("\nOVERALL VERDICT: FAILURES DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
