# RC13: Execution Runbook & Verification Guide

## 1. Local Environment Verification
Run automated code quality and gate validation:

```bash
# 1. Check documentation formatting and STATUS invariants
python scripts/docs_lint.py

# 2. Check code style and formatting
ruff check .

# 3. Type checking
mypy scripts/rc13 tests/unit/test_rc13_*.py tests/release/test_rc13_*.py

# 4. Run RC13 unit and release test suites
pytest tests/unit/test_rc13_*.py tests/release/test_rc13_*.py
```

## 2. Founder Live Trial Verification Runbook
Once physical trials and cloud services are conducted by the founder:
1. **Collect Raw Logs & Metrics**:
   - Extract real VTO job outputs and latency timings into JSON format.
   - Extract real user cohort metrics into JSON format.
2. **Execute Automated Evaluators**:
   ```bash
   python scripts/rc13/validate_evidence.py --input <path_to_evidence.json>
   python scripts/rc13/evaluate_vto.py --input <path_to_vto_jobs.json>
   python scripts/rc13/evaluate_product_metrics.py --input <path_to_pilot_metrics.json>
   python scripts/rc13/evaluate_release_gates.py --input <path_to_gates_summary.json>
   ```
3. **Produce Authentic Evidence Cards**:
   - Write human evidence cards directly in `docs/evidence/` with `collected_by: founder` and `raw_data: <cmd_output>`.
