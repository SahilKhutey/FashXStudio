# Quality Evaluation Test Plan

## 1. Test Suite Architecture

The Phase 07.7 evaluation framework is validated across five dedicated automated test suites:

1. **`test_dataset_and_permissions.py`** (`DATA-*` & `DIV-*`): Validates manifest integrity, Pydantic schemas, permission verification, and partition separation.
2. **`test_runner_and_pipeline.py`** (`EVAL-*`): Validates pipeline execution, negative case interception, and latency percentile calculation.
3. **`test_ratings_and_scoring.py`** (`QUAL-*`): Validates 6-dimension rubric weighting, multi-reviewer aggregation, and critical issue hard gates.
4. **`test_category_gate.py`** (`GATE-*`): Validates category threshold analysis and state transitions (`APPROVED_LIMITED`, `BLOCKED`, `EVALUATING`).
5. **`test_image_metrics.py`** (`METRIC-*`): Validates SSIM and color delta algorithms on identical, perturbed, and mismatched inputs.

---

## 2. Test Execution Command

```bash
python tests/unit/tryon/evaluation/run_all_evaluation_tests.py
```
All tests run synchronously via generator stepping to prevent Windows event loop IOCP deadlocks.
