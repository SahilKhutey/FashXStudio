# Phase 06.2 — Confidence Scoring and Review Policy

## 1. Operating Thresholds

| Confidence Score | Policy Action | Criteria |
|---|---|---|
| **0.95 – 1.00** | Auto-Accept Eligible | High-confidence deterministic rule or verified merchant field with valid evidence. |
| **0.80 – 0.94** | Auto-Accept for Low-Risk Attributes | Accepted automatically only for low-risk fields (`fit_type`, `color`, `garment_type`, `pattern`). Sensitive fields require human review. |
| **0.60 – 0.79** | Human Review Required | Routed to the human review queue with flag `LOW_CONFIDENCE`. |
| **< 0.60** | Rejected / Marked Unknown | Inferred value discarded or marked `UNKNOWN`. |

## 2. Review Trigger Flags

- `LOW_CONFIDENCE`: Confidence score below threshold for the attribute tier.
- `MISSING_EVIDENCE`: Attribute lacks traceable source span or field.
- `CONFLICTING_EVIDENCE`: Title rule conflicts with merchant-provided attribute (e.g. Title says "Black", Merchant says "Navy Blue").
- `FABRIC_UNVERIFIED`: Fabric claim lacks explicit source verification.
- `CATEGORY_AMBIGUOUS`: Unresolved merchant category string.
