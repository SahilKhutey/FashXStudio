"""Master test runner for Phase 07.7 VTO Quality Evaluation test suites."""

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


test_dataset = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "evaluation" / "test_dataset_and_permissions.py",
    "test_dataset_and_permissions",
)
test_runner = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "evaluation" / "test_runner_and_pipeline.py",
    "test_runner_and_pipeline",
)
test_ratings = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "evaluation" / "test_ratings_and_scoring.py",
    "test_ratings_and_scoring",
)
test_gate = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "evaluation" / "test_category_gate.py",
    "test_category_gate",
)
test_metrics = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "evaluation" / "test_image_metrics.py",
    "test_image_metrics",
)

MODULES = [
    (test_dataset, "Dataset Manifest, Permissions & Diversity (DATA / DIV)"),
    (test_runner, "Evaluation Pipeline & Benchmark Metrics (EVAL)"),
    (test_ratings, "Human Quality Ratings & Consensus (QUAL)"),
    (test_gate, "Category Quality Gates & Policy Enforcement (GATE)"),
    (test_metrics, "Automated Objective Image Metrics (METRIC)"),
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
    print("RUNNING PHASE 07.7 VTO QUALITY EVALUATION TEST SUITE")
    print("=" * 75)

    total_passed = 0
    total_failed = 0

    for mod, name in MODULES:
        p, f = run_module(mod, name)
        total_passed += p
        total_failed += f

    print("\n" + "=" * 75)
    print(
        f"PHASE 07.7 SUMMARY: {total_passed} passed, {total_failed} failed, total {total_passed + total_failed}"
    )
    print("=" * 75)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
