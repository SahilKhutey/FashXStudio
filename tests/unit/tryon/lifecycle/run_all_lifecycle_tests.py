"""Direct test runner for Phase 07.4 VTO job lifecycle unit tests."""

from __future__ import annotations

import inspect
import os
import sys

# Ensure backend and root are in python path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))

# Environment safeguards for sandbox
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"

import tests.unit.tryon.lifecycle.test_accept_job_use_case as mod_accept
import tests.unit.tryon.lifecycle.test_idempotency_lifecycle as mod_idempotency
import tests.unit.tryon.lifecycle.test_output_validation as mod_output
import tests.unit.tryon.lifecycle.test_provider_attempts_and_worker as mod_worker
import tests.unit.tryon.lifecycle.test_state_machine as mod_state


def run_sync(coro):
    stack = [coro]
    val = None
    while stack:
        curr = stack[-1]
        try:
            yielded = curr.send(val)
            val = None
            if hasattr(yielded, "send"):
                stack.append(yielded)
        except StopIteration as e:
            stack.pop()
            val = e.value
    return val


MODULES = [
    ("Idempotency & Request Hashing", mod_idempotency),
    ("Output Validation & SSRF Safeguards", mod_output),
    ("Job State Machine & Transitions", mod_state),
    ("AcceptJob Use Case & Security Gates", mod_accept),
    ("Provider Attempts & Worker Execution", mod_worker),
]


def run_suite():
    total_passed = 0
    total_failed = 0

    print("======================================================================")
    print("           RUNNING PHASE 07.4 VTO LIFECYCLE TEST SUITE                ")
    print("======================================================================")

    for suite_name, mod in MODULES:
        print(f"\n--- Suite: {suite_name} ---")
        test_funcs = [
            (name, getattr(mod, name))
            for name in dir(mod)
            if name.startswith("test_") and callable(getattr(mod, name))
        ]

        for name, fn in test_funcs:
            try:
                if inspect.iscoroutinefunction(fn):
                    coro = fn()
                    run_sync(coro)
                else:
                    fn()
                total_passed += 1
                print(f"  [PASS] {name}")
            except Exception as e:
                total_failed += 1
                print(f"  [FAIL] {name}: {type(e).__name__}: {e}")

    print("\n======================================================================")
    print(f"TOTAL RESULTS: {total_passed} PASSED, {total_failed} FAILED (Total: {total_passed + total_failed})")
    print("======================================================================")

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_suite()
