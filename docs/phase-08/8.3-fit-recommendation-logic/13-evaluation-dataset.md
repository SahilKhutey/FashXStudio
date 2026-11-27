# 13 — Evaluation Dataset Specification (`evaluation/dataset.py`)

## Provenance & Label Taxonomy

Each case (`EvaluationDatasetCase`) records: `case_id`, `dataset_version`, `split` (`DEVELOPMENT`, `VALIDATION`, `TEST`), `shopper_key`, `merchant_id`, `product_id`, `merchant_offer_id`, `category`, `variant_id`, `size_chart_revision`, `measurement_basis`, `expected_label` (`RECOMMENDED_SIZE`, `ALTERNATIVE_ACCEPTABLE`, `NO_MATCH`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`, `UNSUPPORTED_CATEGORY`), `expected_size`, `acceptable_sizes`, `reviewer_id`, `labelled_at`, and `evidence_reference`.

## Leakage & Split Isolation

`validate_dataset_splits` rejects empty datasets, missing human reviewer IDs, missing evidence references, non-TZ-aware timestamps, and any `shopper_key` or `merchant_id:product_id` appearing in multiple splits.

## Status Note (Rule 2)

An engineering fixture file exists at `tests/fixtures/fit_evaluation/fixture_cases.json` solely for unit-testing dataset parsing and split guards (`is_synthetic: true`). Consented real-world manually labelled cases (target: 100–200 pilot, 300–500 initial evaluation) remain outstanding prior to production rollout.
