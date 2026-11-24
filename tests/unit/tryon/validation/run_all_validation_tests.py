"""Direct test runner for Phase 07.3 VTO input validation unit tests."""

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

import tests.unit.tryon.validation.test_combined_validator as mod_combined
import tests.unit.tryon.validation.test_garment_validator as mod_garment
import tests.unit.tryon.validation.test_image_inspector as mod_inspector
import tests.unit.tryon.validation.test_shopper_validator as mod_shopper
import tests.unit.tryon.validation.test_time_of_use_guard as mod_tou
from fashx.tryon.validation.config import ImageValidationConfig
from fashx.tryon.validation.image_inspector import ImageInspector


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
    ("ImageInspector (IMG)", mod_inspector),
    ("ShopperValidator (SHP)", mod_shopper),
    ("GarmentValidator (GAR)", mod_garment),
    ("CombinedValidator (COM)", mod_combined),
    ("TimeOfUseGuard (TOU)", mod_tou),
]


def run_suite():
    total_passed = 0
    total_failed = 0
    inspector_fixture = ImageInspector(ImageValidationConfig())

    print("======================================================================")
    print("        RUNNING PHASE 07.3 VTO INPUT VALIDATION TEST SUITE           ")
    print("======================================================================")

    for suite_name, mod in MODULES:
        print(f"\n--- Suite: {suite_name} ---")
        test_funcs = [
            (name, getattr(mod, name))
            for name in dir(mod)
            if name.startswith("test_") and callable(getattr(mod, name))
        ]

        for name, fn in test_funcs:
            sig = inspect.signature(fn)
            kwargs = {}
            if "inspector" in sig.parameters:
                kwargs["inspector"] = inspector_fixture

            try:
                if inspect.iscoroutinefunction(fn):
                    coro = fn(**kwargs)
                    run_sync(coro)
                else:
                    fn(**kwargs)
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
