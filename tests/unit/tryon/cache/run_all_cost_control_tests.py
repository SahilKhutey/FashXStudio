"""Master test runner for Phase 07.6 Caching, Rate Limiting, and Cost Controls."""

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


test_keys = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "cache" / "test_cache_keys.py",
    "test_cache_keys",
)
test_service = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "cache" / "test_cache_service.py",
    "test_cache_service",
)
test_limits = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "limits" / "test_rate_limits.py",
    "test_rate_limits",
)
test_billing = load_module_from_file(
    ROOT / "tests" / "unit" / "tryon" / "billing" / "test_budget_and_usage.py",
    "test_budget_and_usage",
)

MODULES = [
    (test_keys, "Cache Key Identity & Collisions (CACHE-001..020)"),
    (test_service, "Cache Service & Isolation (CACHE-SVC-001..007)"),
    (test_limits, "Rate Limits & Concurrency (RATE-001..008)"),
    (test_billing, "Budgets, Usage Ledger & Monitoring (BUDGET/USAGE/MONITOR)"),
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
        is_parametrized = False

        if hasattr(func, "pytestmark"):
            for mark in func.pytestmark:
                if mark.name == "parametrize":
                    is_parametrized = True
                    argnames, argvalues = mark.args
                    if isinstance(argnames, str):
                        argnames = [a.strip() for a in argnames.split(",")]
                    for vals in argvalues:
                        if not isinstance(vals, tuple):
                            vals = (vals,)
                        kwargs = dict(zip(argnames, vals, strict=False))
                        call_repr = (
                            f"{func_name}({', '.join(f'{k}={v}' for k, v in kwargs.items())})"
                        )
                        try:
                            res = func(**kwargs)
                            if inspect.iscoroutine(res):
                                run_sync(res)
                            print(f"  [PASS] {call_repr}")
                            passed += 1
                        except Exception as e:
                            print(f"  [FAIL] {call_repr}: {e}")
                            traceback.print_exc()
                            failed += 1

        if not is_parametrized:
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
    print("RUNNING PHASE 07.6 CACHING AND COST CONTROL TEST SUITE")
    print("=" * 75)

    total_passed = 0
    total_failed = 0

    for mod, name in MODULES:
        p, f = run_module(mod, name)
        total_passed += p
        total_failed += f

    print("\n" + "=" * 75)
    print(
        f"PHASE 07.6 SUMMARY: {total_passed} passed, {total_failed} failed, total {total_passed + total_failed}"
    )
    print("=" * 75)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
