# 07 — Confidence Methodology & Hard Gates

## Internal Evidence Completeness Formula

$$C = 0.25P + 0.25S + 0.20K + 0.20M + 0.10V$$

Where each dimension lies in $[0, 1]$:
- $P$: `profile_quality` (required measurement completeness and freshness)
- $S$: `chart_quality` (chart presence, basis clarity, and freshness)
- $K$: `category_quality` (validated and enabled category policy)
- $M$: `measurement_compatibility` (overlapping required measurement fields)
- $V$: `variant_validity` (purchasable variant availability)

## Non-Calibration Disclosure Rule

- `ConfidenceSummary.type` is fixed to `INTERNAL_EVIDENCE_SCORE` and `display_to_shopper` defaults to `False`.
- Hard evidence eligibility gates in `validate_evidence` and `may_recommend` ALWAYS take precedence over numeric thresholds; an ineligible state cannot be overridden by a high score.
- The mobile client hides internal scores and must only display calibrated scores if empirical calibration on independently labelled outcomes is demonstrated.
