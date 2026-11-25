"""Consolidated Phase 07 Master Exit Gate Test Runner.

Executes all Phase 07 test suites across all sub-phases:
- Phase 07.3: Input Validation Suite
- Phase 07.4: VTO Job Lifecycle Suite
- Phase 07.5: State Machine & Reliability Suite
- Phase 07.6: Caching & Cost Controls Suite
- Phase 07.7: Quality Evaluation & Category Gates Suite
- Phase 07.8: Visual Try-On vs Fit Prediction Separation Suite
- Phase 07.9: Production Exit Gate Integration Suite
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
backend_path = ROOT / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Environment safeguards for sandbox
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


def run_subphase_script(script_path: Path, label: str) -> tuple[int, int]:
    print("\n=======================================================")
    print(f"RUNNING SUB-PHASE: {label} ({script_path.name})")
    print("=======================================================")
    import subprocess

    start = time.perf_counter()
    proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    duration = time.perf_counter() - start
    output = proc.stdout + proc.stderr

    # Parse passed and failed from output
    import re

    passed = 0
    failed = 0
    m_pass = re.findall(r"(\d+)\s+passed", output, re.IGNORECASE)
    m_fail = re.findall(r"(\d+)\s+failed", output, re.IGNORECASE)
    if m_pass:
        passed = int(m_pass[-1])
    if m_fail:
        failed = int(m_fail[-1])

    if proc.returncode != 0 and failed == 0:
        failed = 1
        print(f"FAILED (code {proc.returncode}):\n{output}")
    else:
        # Print summary lines
        summary_lines = [
            l
            for l in output.strip().split("\n")
            if "summary" in l.lower() or "passed" in l.lower() or "results" in l.lower()
        ]
        for l in summary_lines[-2:]:
            print(f"  {l}")
        print(f"  Execution time: {duration:.2f}s")
    return passed, failed


def main() -> int:
    overall_start = time.perf_counter()
    suites = [
        (
            ROOT / "tests" / "unit" / "tryon" / "validation" / "run_all_validation_tests.py",
            "Phase 07.3 Input Validation",
        ),
        (
            ROOT / "tests" / "unit" / "tryon" / "lifecycle" / "run_all_lifecycle_tests.py",
            "Phase 07.4 Job Lifecycle",
        ),
        (
            ROOT / "tests" / "unit" / "tryon" / "lifecycle" / "run_all_reliability_tests.py",
            "Phase 07.5 Reliability & Failure Handling",
        ),
        (
            ROOT / "tests" / "unit" / "tryon" / "cache" / "run_all_cost_control_tests.py",
            "Phase 07.6 Caching & Cost Controls",
        ),
        (
            ROOT / "tests" / "unit" / "tryon" / "evaluation" / "run_all_evaluation_tests.py",
            "Phase 07.7 Quality Evaluation & Category Gates",
        ),
        (
            ROOT / "tests" / "unit" / "tryon" / "separation" / "run_all_separation_tests.py",
            "Phase 07.8 VTO & Fit Prediction Separation",
        ),
    ]

    total_passed = 0
    total_failed = 0

    print("#######################################################")
    print("      FASHXSTUDIO PHASE 07 PRODUCTION EXIT GATE        ")
    print("#######################################################")

    for path, label in suites:
        p, f = run_subphase_script(path, label)
        total_passed += p
        total_failed += f

    # Run 07.9 integration exit gate module directly
    exit_gate_mod = load_module_from_file(
        ROOT / "tests" / "unit" / "tryon" / "exit_gate" / "test_phase07_exit_gate.py",
        "test_phase07_exit_gate",
    )
    p_exit, f_exit = run_test_module(exit_gate_mod, "Phase 07.9 Exit Gate Integration Suite")
    total_passed += p_exit
    total_failed += f_exit

    overall_duration = time.perf_counter() - overall_start

    print("\n#######################################################")
    print("               FINAL EXIT GATE SUMMARY                 ")
    print("#######################################################")
    print("  Total Sub-phases Evaluated: 7")
    print(f"  Total Tests Passed:         {total_passed}")
    print(f"  Total Tests Failed:         {total_failed}")
    print(f"  Total Wall-clock Time:      {overall_duration:.2f}s")
    if total_failed == 0:
        print("  Status:                     ALL PHASE 07 GATES PASSED [LOCAL / SANDBOX]")
        print("#######################################################\n")
        return 0
    else:
        print("  Status:                     EXIT GATE REJECTED - FAILURES DETECTED")
        print("#######################################################\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
