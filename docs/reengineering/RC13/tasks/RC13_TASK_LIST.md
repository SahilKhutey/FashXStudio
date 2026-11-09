# RC13 & RC13.1 Task List & Remediation Status

## Track 1: Baseline Reconciliation & Branch Integration
- [x] Integrate PRs #30, #31, #32, and #33 into `main` (`050b504`).
- [x] Create branch `recovery/rc13.1-governance-correction` from `main`.
- [x] Reconcile stale post-merge instructions in `00_BASELINE_RECONCILIATION.md` and `13_FINAL_DECISION.md`.
- [x] Reconcile metric contract strictly to `docs/pilot/pilot-plan.md`.

## Track 2: Evaluator Engine Governance Correction (RC13.1)
- [x] Upgrade [`scripts/rc13/validate_evidence.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/validate_evidence.py):
  - SHA-256 byte digest verification against actual source files on disk (`--verify-files`).
  - Rejection of placeholder/unauthorized reviewers.
  - Rejection of future timestamps.
  - PII quarantine scanner and synthetic data rejection.
- [x] Upgrade [`scripts/rc13/evaluate_product_metrics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_product_metrics.py):
  - Strictly aligned with 12 Must-Haves (M1–M5), 10 Should-Haves (S1–S4), and 7 Hard Stop Rules.
  - Fail-closed evaluation: missing must-haves trigger HOLD; critical failures trigger PIVOT OR STOP.
- [x] Upgrade [`scripts/rc13/evaluate_vto.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_vto.py):
  - Reconciled dual-tier standards: Contractual Gate Ceiling (P95 $\le 45\text{s}$, completion $\ge 90\%$, defect $\le 15\%$, rating $\ge 3.8$) vs Operational Targets (P95 $\le 30\text{s}$, completion $\ge 95\%$, defect $\le 10\%$, rating $\ge 4.0$).
  - Deduplicated defect job counting invariant.
- [x] Upgrade [`scripts/rc13/evaluate_release_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_release_gates.py):
  - Cryptographic and disk verification (`--verify-on-disk`).
  - G1–G6 fail-closed governance (GO, FIX, HOLD).

## Track 3: Test Verification (35 Tests Passing)
- [x] `tests/unit/test_rc13_evidence.py`: 10 tests passed (including SHA-256 mismatch, file existence, placeholder reviewer).
- [x] `tests/unit/test_rc13_product_metrics.py`: 7 tests passed (frozen must-haves, should-haves, stop rules, fail-closed HOLD).
- [x] `tests/unit/test_rc13_vto.py`: 7 tests passed (gate ceiling vs target, defect deduplication, mock rejection).
- [x] `tests/unit/test_rc13_release_gates.py`: 8 tests passed (all gates PASS -> GO, missing file on disk -> HOLD, placeholder -> HOLD).
- [x] `tests/release/test_rc13_final_gates.py`: 3 tests passed (pre-pilot baseline HOLD, founder evidence GO, failed gate FIX).

## Track 4: Documentation & Audit Remediation (RC13.1)
- [x] `docs/reengineering/RC13/00_BASELINE_RECONCILIATION.md`
- [x] `docs/reengineering/RC13/01_VALIDATION_STRATEGY.md`
- [x] `docs/reengineering/RC13/02_TECHNICAL_VALIDATION.md`
- [x] `docs/reengineering/RC13/03_PRODUCT_VALIDATION.md`
- [x] `docs/reengineering/RC13/04_VTO_EVALUATION.md`
- [x] `docs/reengineering/RC13/05_CATALOG_AND_COMMERCE_VALIDATION.md`
- [x] `docs/reengineering/RC13/06_MARKET_AND_COMPETITOR_RESEARCH.md`
- [x] `docs/reengineering/RC13/07_CUSTOMER_ACQUISITION_AND_RETENTION.md`
- [x] `docs/reengineering/RC13/08_UNIT_ECONOMICS.md`
- [x] `docs/reengineering/RC13/09_PRIVACY_SECURITY_AND_LEGAL.md`
- [x] `docs/reengineering/RC13/10_RELEASE_GATES.md`
- [x] `docs/reengineering/RC13/11_TEST_PLAN.md`
- [x] `docs/reengineering/RC13/12_EXECUTION_RUNBOOK.md`
- [x] `docs/reengineering/RC13/13_FINAL_DECISION.md`
- [x] `docs/reengineering/RC13/14_GOVERNANCE_CORRECTION_AUDIT.md`
- [x] `docs/reengineering/RC13/README.md`

## Track 5: Governance & Integrity Assurance
- [x] Zero edits to `docs/evidence/`, `docs/provenance.md`, or `docs/release/gates.md` (Rule 1).
- [x] Zero simulated numbers or false clearance claims (Rule 2).
- [x] Documentation lint (`docs_lint.py`) clean.
- [x] Ruff check clean.
- [x] Mypy clean.
