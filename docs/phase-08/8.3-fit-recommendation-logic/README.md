# Phase 08.3 — Fit Recommendation Logic

## Objective

Develop a deterministic, explainable, evidence-based backend and mobile fit recommendation service that compares an authenticated shopper's consented body measurements against the exact merchant product's verified size chart. The service recommends a size only when sufficient, fresh, compatible, and authorized evidence exists; otherwise it returns an explicit abstention outcome (`INSUFFICIENT_INFORMATION`, `UNSUPPORTED_CATEGORY`, `STALE_DATA`, `CONFLICTING_DATA`, or `NO_AVAILABLE_SIZE`).

## Scope

1. Measurement matching against `BODY` vs `GARMENT` bases (`measurement_matcher.py`)
2. Versioned category-specific measurement requirements (`category_policy.py`)
3. Sourced, evidence-referenced ease and intended-fit rules (`ease_policy.py`)
4. Merchant-specific product, offer, and chart-revision isolation (`service.py`, `evidence.py`)
5. First-class missing, stale, conflicting, and unauthorized evidence handling (`evidence.py`)
6. Internal evidence completeness score + hard eligibility gates (`confidence.py`)
7. Deterministic candidate evaluation and abstention policy (`decision.py`)
8. Approved non-guarantee explanations and disclosures (`explanations.py`)
9. Authenticated REST endpoints & immutable snapshots (`router.py`, `repository.py`, migration `0058`)
10. Mobile product-detail fit guidance separated from Virtual Try-On (`mobile/src/features/fit/`)
11. Split-isolated evaluation dataset & calibration metrics (`evaluation/`)
12. Snapshot-bound shopper fit feedback with ownership & review triage (`feedback.py`)

## Core Architectural Rules

- Body measurements and finished garment measurements are strictly distinct data types (`MeasurementBasis.BODY` vs `MeasurementBasis.GARMENT`).
- Every recommendation is bound to the exact `merchant_id`, `merchant_product_id`, `merchant_offer_id`, `size_chart_id`, and `size_chart_revision`.
- Merchant size labels (`S`, `M`, `L`) are never assumed equivalent across brands or merchants.
- Missing, stale, conflicting, or unauthorized data fails closed into explicit abstention.
- Internal evidence scores (`display_to_shopper = False`) are never displayed as calibrated probabilities until empirical calibration is proven.
- Virtual Try-On outputs are never accepted as physical fit evidence (`FitEvidenceSecurityError`).
- Fit guidance never claims a fit guarantee (`fit_guaranteed = False`).

## Initial Release Scope

- Launch category enabled by default: `TSHIRTS` (`BODY` measurement basis, requiring `CHEST`).
- Unvalidated categories (`TROUSERS`, `SHIRTS`, `KURTAS`, `TOPS`, `JEANS`, `DRESSES`, `SAREES`, `LEHENGAS`) remain `enabled = False` until merchant chart coverage and human-labelled accuracy gates are validated.
- Default `EasePolicyRegistry` contains zero invented ease rules; garment-basis matching requires explicit `EaseRule` approval backed by evidence references.

## Limitations

Size guidance estimates chart alignment from published merchant data and shopper-entered measurements. It does not guarantee physical fit, comfort, stretch behaviour, or garment appearance.

## Documents

1. [01-architecture.md](01-architecture.md)
2. [02-measurement-matching.md](02-measurement-matching.md)
3. [03-category-fit-policies.md](03-category-fit-policies.md)
4. [04-ease-and-intended-fit.md](04-ease-and-intended-fit.md)
5. [05-merchant-specific-sizing.md](05-merchant-specific-sizing.md)
6. [06-missing-data-and-abstention.md](06-missing-data-and-abstention.md)
7. [07-confidence-methodology.md](07-confidence-methodology.md)
8. [08-recommendation-decision-policy.md](08-recommendation-decision-policy.md)
9. [09-explanation-and-disclosure.md](09-explanation-and-disclosure.md)
10. [10-api-contracts.md](10-api-contracts.md)
11. [11-database-and-versioning.md](11-database-and-versioning.md)
12. [12-feedback-workflow.md](12-feedback-workflow.md)
13. [13-evaluation-dataset.md](13-evaluation-dataset.md)
14. [14-accuracy-and-calibration.md](14-accuracy-and-calibration.md)
15. [15-privacy-and-security.md](15-privacy-and-security.md)
16. [16-test-plan.md](16-test-plan.md)
17. [17-execution-report.md](17-execution-report.md)
18. [18-release-checklist.md](18-release-checklist.md)
