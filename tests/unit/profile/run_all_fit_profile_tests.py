"""Master Test Runner for Phase 08.2 Shopper Fit Profile."""

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

os.environ.setdefault("ENV", "test")
os.environ.setdefault("AUTH_MODE", "local")
os.environ.setdefault("AUTH_JWT_SECRET", "test-secret-key-at-least-32-chars-long")
os.environ.setdefault("AUTH_ISSUER", "fashx-test")
os.environ.setdefault("AUTH_AUDIENCE", "fashx-api")
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
                    # Handle pytest caplog-dependent test cleanly when invoked outside pytest
                    sig = getattr(fn, "__code__", None)
                    if sig and "caplog" in sig.co_varnames[: sig.co_argcount]:
                        import logging

                        class _SimpleCaplog:
                            def __init__(self):
                                self.records = []

                            @property
                            def text(self):
                                return "\n".join(r.getMessage() for r in self.records)

                            def at_level(self, level):
                                cap = self

                                class _Ctx:
                                    def __enter__(self_inner):
                                        self_inner._handler = logging.Handler()
                                        self_inner._handler.setLevel(level)
                                        self_inner._handler.emit = lambda r: cap.records.append(r)
                                        logging.getLogger().addHandler(self_inner._handler)

                                    def __exit__(self_inner, *args):
                                        logging.getLogger().removeHandler(self_inner._handler)

                                return _Ctx()

                        fn(_SimpleCaplog())
                    else:
                        fn()
                    passed += 1
                    print(f"  [PASS] {attr_name}")
                except Exception as exc:
                    failed += 1
                    print(f"  [FAIL] {attr_name}: {exc}")
                    traceback.print_exc()
    return passed, failed


def main() -> int:
    start_time = time.time()
    this_dir = Path(__file__).parent

    test_files = [
        (
            "test_fit_policy_and_definitions.py",
            "Phase 08.2 - Category Policies & Measurement Guidance",
        ),
        (
            "test_fit_schemas_units_validation.py",
            "Phase 08.2 - Schemas, Units & Range Validation",
        ),
        (
            "test_fit_preferences_and_brand_independence.py",
            "Phase 08.2 - Fit Preferences & Brand-Size Independence",
        ),
        (
            "test_fit_profile_service_history_privacy.py",
            "Phase 08.2 - Service, History, Consent & Zero-PII Privacy",
        ),
        (
            "test_fit_profile_api.py",
            "Phase 08.2 - Authenticated Fit Profile REST API",
        ),
    ]

    total_passed = 0
    total_failed = 0
    print("=======================================================")
    print("FASHXSTUDIO PHASE 08.2 MASTER FIT PROFILE TEST RUNNER")
    print("=======================================================")

    for fname, label in test_files:
        fpath = this_dir / fname
        mod_name = f"tests.unit.profile.{fname.replace('.py', '')}"
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
    print("PHASE 08.2 FIT PROFILE TEST RESULTS SUMMARY")
    print("=======================================================")
    print(f"Total Tests Run: {total_passed + total_failed}")
    print(f"Passed:          {total_passed}")
    print(f"Failed:          {total_failed}")
    print(f"Elapsed Time:    {elapsed:.2f}s")
    print("=======================================================")
    if total_failed == 0 and total_passed > 0:
        print("\nOVERALL VERDICT: ALL TESTS PASSED (100% GREEN)")
        return 0
    print("\nOVERALL VERDICT: FAILURES DETECTED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
