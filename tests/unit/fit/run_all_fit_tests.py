"""Master test runner for Phase 08.3 Fit Recommendation Logic."""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(_ROOT / "backend"))

os.environ.setdefault("ENV", "test")
os.environ.setdefault("AUTH_MODE", "local")
os.environ.setdefault("AUTH_JWT_SECRET", "test-secret-key-at-least-32-chars-long")
os.environ.setdefault("AUTH_ISSUER", "fashx-test")
os.environ.setdefault("AUTH_AUDIENCE", "fashx-api")
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"


def _load_module(path: Path, mod_name: str):
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_THIS_DIR = Path(__file__).resolve().parent
MODULES = [
    (
        "Phase 08.3 - Matcher, Category Policy & Ease",
        _load_module(_THIS_DIR / "test_fit_matcher_and_policy.py", "fit_test_matcher"),
    ),
    (
        "Phase 08.3 - Evidence Gates, Confidence, Decision & Explanations",
        _load_module(
            _THIS_DIR / "test_fit_evidence_confidence_decision.py",
            "fit_test_evidence",
        ),
    ),
    (
        "Phase 08.3 - Evaluation Dataset, Metrics & Shopper Feedback",
        _load_module(_THIS_DIR / "test_fit_feedback_and_evaluation.py", "fit_test_eval"),
    ),
    (
        "Phase 08.3 - Authenticated Fit API & Security",
        _load_module(_THIS_DIR / "test_fit_api.py", "fit_test_api"),
    ),
]


def main() -> int:
    start = time.monotonic()
    total = 0
    passed = 0
    failed = 0

    print("=======================================================")
    print("FASHXSTUDIO PHASE 08.3 FIT RECOMMENDATION TEST RUNNER")
    print("=======================================================")

    for title, mod in MODULES:
        print("\n=======================================================")
        print(f"RUNNING: {title}")
        print("=======================================================")
        test_fns = [
            getattr(mod, name)
            for name in sorted(dir(mod))
            if name.startswith("test_") and callable(getattr(mod, name))
        ]
        for fn in test_fns:
            total += 1
            try:
                fn()
                passed += 1
                print(f"  [PASS] {fn.__name__}")
            except Exception as exc:
                failed += 1
                print(f"  [FAIL] {fn.__name__}: {exc}")

    elapsed = time.monotonic() - start
    print("\n=======================================================")
    print("PHASE 08.3 FIT RECOMMENDATION TEST RESULTS SUMMARY")
    print("=======================================================")
    print(f"Total Tests Run: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Elapsed Time:    {elapsed:.2f}s")
    print("=======================================================")
    if failed:
        print("OVERALL VERDICT: FAILURES DETECTED")
        return 1
    print("OVERALL VERDICT: ALL TESTS PASSED (100% GREEN)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
