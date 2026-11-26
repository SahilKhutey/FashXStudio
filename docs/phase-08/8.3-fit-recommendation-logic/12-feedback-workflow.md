# 12 — Feedback Workflow & Governance (`feedback.py`)

## Shopper Feedback Intake

- Supported `FitFeedbackReason` codes: `SIZE_TOO_SMALL`, `SIZE_TOO_LARGE`, `FIT_TOO_TIGHT`, `FIT_TOO_LOOSE`, `LENGTH_TOO_SHORT`, `LENGTH_TOO_LONG`, `SIZE_CHART_INACCURATE`, `RECOMMENDATION_UNHELPFUL`, `OTHER`.
- Captures `purchase_status`, `tried_on`, `kept_item`, `selected_different_size`, and optional `comment`.
- Backend derives `product_id`, `merchant_id`, `merchant_offer_id`, `size_chart_id`, `size_chart_revision`, and `recommended_size` exclusively from the stored `FitRecommendation` snapshot owned by the authenticated shopper.

## Triage, Safety & Deletion

- Submissions with `tried_on=False` are stored as `feedback_basis="RECOMMENDATION_ONLY"` and `review_status="UNVERIFIED"`.
- Duplicate submissions per `(recommendation_id, user_id)` raise `DuplicateFitFeedbackError` (`409 Conflict`).
- Human triage (`triage_feedback`) classifies issues without ever automatically altering fit or ease rules.
- Shopper deletion clears free-text comments and soft-deletes feedback (`deleted_at`); full account erasure deletes `fit_feedback` and `fit_recommendations` via `ACCOUNT_TABLES`.
