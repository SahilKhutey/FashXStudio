"""Master test runner for Phase 07.8 VTO and Fit Prediction Separation test suites."""

from __future__ import annotations

import importlib.util
import inspect
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
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


test_presentation = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "separation" / "test_presentation_policy.py",
    "test_presentation_policy",
)
test_size = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "separation" / "test_size_charts.py",
    "test_size_charts",
)
test_fit = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "separation" / "test_fit_recommendations.py",
    "test_fit_recommendations",
)
test_claims = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "separation" / "test_claims_policy.py",
    "test_claims_policy",
)
test_feedback = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "separation" / "test_shopper_feedback.py",
    "test_shopper_feedback",
)

MODULES = [
    (test_presentation, "Visual Try-On Disclosure & Labels (DISC-001..010)"),
    (test_size, "Merchant Size Charts & Provenance (SIZE-001..014)"),
    (test_fit, "Evidence-Backed Fit Recommendations (FIT-001..018)"),
    (test_claims, "Claims & Prohibited Copy Policies (COPY-001..010)"),
    (test_feedback, "Shopper Reporting & Quality Triage (FDBK-001..015)"),
]


def run_sync(coro):
    """Run an async coroutine synchronously using generator stepping to avoid Windows IOCP deadlocks."""
    stack = [coro]
    val = None
    while stack:
        curr = stack[-1]
        try:
            if inspect.iscoroutine(curr):
                nxt = curr.send(val)
                val = None
                if inspect.iscoroutine(nxt):
                    stack.append(nxt)
            else:
                stack.pop()
        except StopIteration as e:
            val = e.value
            stack.pop()
    return val


def run_module(module, name):
    print(f"\n--- Suite: {name} ---")
    passed = 0
    failed = 0

    test_funcs = [
        getattr(module, attr)
        for attr in dir(module)
        if attr.startswith("test_") and callable(getattr(module, attr))
    ]

    for func in test_funcs:
        func_name = func.__name__
        try:
            res = func()
            if inspect.iscoroutine(res):
                run_sync(res)
            print(f"  [PASS] {func_name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {func_name}: {e}")
            traceback.print_exc()
            failed += 1

    return passed, failed


def main():
    print("=" * 75)
    print("RUNNING PHASE 07.8 VTO & FIT PREDICTION SEPARATION TEST SUITE")
    print("=" * 75)

    total_passed = 0
    total_failed = 0

    for mod, name in MODULES:
        p, f = run_module(mod, name)
        total_passed += p
        total_failed += f

    print("\n" + "=" * 75)
    print(
        f"PHASE 07.8 SUMMARY: {total_passed} passed, {total_failed} failed, total {total_passed + total_failed}"
    )
    print("=" * 75)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
