# RC10: Execution Guide & Workflow

## 1. Branch Strategy
- Branch: `recovery/rc10-product-optimization`
- Target: `main`
- Base: `recovery/rc08-staging-pilot-readiness` (includes `ReleaseConfig` and staging baseline).

## 2. Step-by-Step Execution Sequence
1. **Reconciliation**:
   Inspect branch history, PR status (`gh pr list`), and verify no fabricated metrics exist in active reports.
2. **Tooling & Release Safeguards**:
   - `backend/fashx/core/rc10_timing.py`: synchronous execution timer.
   - `scripts/rc10/evaluate_catalog.py`: catalog quality and clearance validator.
   - `scripts/rc10/evaluate_recommendations.py`: nDCG@k, Precision@k, Recall@k evaluator.
   - `scripts/rc10/validate_metrics.py`: metric record validator rejecting unverified simulated evidence.
   - `scripts/rc10/beta_gates.py`: 9-gate fail-closed beta gate decision engine.
   - `scripts/rc10/summarize_performance.py`: latency percentile summarizer.
   - `scripts/rc10/generate_acceptance_report.py`: markdown acceptance report generator.
3. **Automated Verification**:
   - Run unit tests: `pytest tests/unit/test_rc10_*.py`
   - Run release tests: `pytest tests/release/test_rc10_beta_gates.py`
   - Run integration tests: `pytest tests/integration/test_rc10_*.py`
   - Run security tests: `pytest tests/security/test_rc10_*.py`
   - Run lint & types: `python scripts/docs_lint.py`, `ruff check .`, `mypy .`
4. **Push & PR**:
   - Push to `origin recovery/rc10-product-optimization`.
   - Open Pull Request targeting `main`.
   - Monitor GitHub Actions until all checks pass.
