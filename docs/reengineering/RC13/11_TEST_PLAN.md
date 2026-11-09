# RC13: Comprehensive Test Plan

## 1. Test Architecture
The test suite for RC13 verifies all validation, evaluation, deduplication, and gating logic:

1. **Unit Tests**:
   - [`tests/unit/test_rc13_evidence.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/unit/test_rc13_evidence.py):
     - Validates evidence record structure, missing fields, invalid types/status.
     - Tests PII pattern detection (emails, phones, signed URLs, raw photos).
     - Verifies synthetic evidence rejection for real release gates.
   - [`tests/unit/test_rc13_product_metrics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/unit/test_rc13_product_metrics.py):
     - Tests M1–M5 numeric thresholds.
     - Tests fail on privacy incidents > 0 or sub-threshold metrics.
     - Tests fail-closed HOLD on missing/unknown data.
   - [`tests/unit/test_rc13_vto.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/unit/test_rc13_vto.py):
     - Tests live GPU provider requirement (rejects mock/synthetic by default).
     - Tests defect deduplication invariant across multiple tags on single jobs.
     - Tests completion rate and P95 latency evaluation.
   - [`tests/unit/test_rc13_release_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/unit/test_rc13_release_gates.py):
     - Tests 6/6 PASS -> GO decision.
     - Tests FAIL -> FIX decision.
     - Tests unmeasured/missing -> HOLD decision.
     - Tests missing reviewer or evidence reference -> HOLD decision.

2. **Release Integration Tests**:
   - [`tests/release/test_rc13_final_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/release/test_rc13_final_gates.py):
     - Verifies that the current repository baseline (without human evidence cards) evaluates to `HOLD`.
     - Verifies that a full set of verified founder evidence evaluates to `GO`.
     - Verifies that a failed gate triggers `FIX`.

## 2. Test Execution
```bash
pytest tests/unit/test_rc13_*.py tests/release/test_rc13_*.py
```
