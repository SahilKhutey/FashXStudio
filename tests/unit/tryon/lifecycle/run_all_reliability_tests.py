"""Master test runner for Phase 07.5 VTO Job States, Failure Handling, and Reliability."""

import inspect
import os
import sys
import traceback

# Ensure root and backend are at the top of sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
backend_path = os.path.join(ROOT, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Environment safeguards for sandbox
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"

import test_cancellation as test_cancellation
import test_leases_and_timeouts as test_leases_and_timeouts
import test_messages_and_duplicates as test_messages_and_duplicates
import test_recovery_and_dlq as test_recovery_and_dlq
import test_retry_policy as test_retry_policy
import test_transitions as test_transitions


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

    # Discover tests
    test_funcs = [
        getattr(module, attr)
        for attr in dir(module)
        if attr.startswith("test_") and callable(getattr(module, attr))
    ]

    for func in test_funcs:
        func_name = func.__name__
        is_parametrized = False

        # Check if pytest.mark.parametrize was applied
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
                        call_repr = f"{func_name}({', '.join(f'{k}={v}' for k, v in kwargs.items())})"
                        try:
                            if inspect.iscoroutinefunction(func):
                                run_sync(func(**kwargs))
                            else:
                                func(**kwargs)
                            print(f"  [PASS] {call_repr}")
                            passed += 1
                        except Exception as e:
                            print(f"  [FAIL] {call_repr}: {e}")
                            traceback.print_exc()
                            failed += 1

        if is_parametrized:
            continue

        # Normal test without parametrize
        try:
            if inspect.iscoroutinefunction(func):
                run_sync(func())
            else:
                func()
            print(f"  [PASS] {func_name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {func_name}: {e}")
            traceback.print_exc()
            failed += 1

    return passed, failed


def main():
    print("=" * 70)
    print("      RUNNING PHASE 07.5 VTO RELIABILITY & FAILURE TEST SUITE      ")
    print("=" * 70)

    suites = [
        (test_transitions, "State Transitions & Invariants (STM)"),
        (test_retry_policy, "Error Classification & Retry Policy (RET)"),
        (test_leases_and_timeouts, "Worker Leases, Timeouts & Concurrency (WKR)"),
        (test_recovery_and_dlq, "Stuck-Job Recovery & Dead Letters (REC / DLQ)"),
        (test_cancellation, "Job Cancellation Workflow (CAN)"),
        (test_messages_and_duplicates, "Duplicate Protection & Shopper Presentation (DUP / MSG)"),
    ]

    total_passed = 0
    total_failed = 0

    for mod, name in suites:
        p, f = run_module(mod, name)
        total_passed += p
        total_failed += f

    print("\n" + "=" * 70)
    print(f"TOTAL RESULTS: {total_passed} PASSED, {total_failed} FAILED (Total: {total_passed + total_failed})")
    print("=" * 70)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
