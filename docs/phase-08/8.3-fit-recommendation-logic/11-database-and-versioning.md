# 11 — Database Schema, Snapshots & Invalidation (`0058`)

## Schema Extensions & Tables (`0058_add_fit_recommendation_snapshot_feedback_eval`)

1. **`fit_recommendations`** (extended): `merchant_id`, `merchant_product_id`, `variant_id`, `size_chart_id`, `size_chart_revision`, `shopper_measurement_revision`, `category_policy_version`, `fit_algorithm_version`, `fit_preference_revision`, `source_permission_revision`, `recommendation_status`, `reason_codes_json`, `internal_confidence_score`, `invalidation_reason`, `invalidated_at`, `expires_at`.
2. **`fit_feedback`** (extended): optional nullable `brand_id`, FK `recommendation_id`, `merchant_id`, `merchant_offer_id`, `size_chart_id`, `size_chart_revision`, `reason`, `purchase_status`, `tried_on`, `kept_item`, `selected_different_size`, `feedback_basis`, `comment`, `review_status`, `reviewed_at`, `deleted_at`, and `uq_fit_feedback_rec_user`.
3. **`fit_recommendation_evidence`**: immutable provenance links (`source_type`, `source_id`, `source_revision`, `measurement_basis`, `evidence_status`).
4. **`fit_recommendation_candidates`**: evaluated variant candidates (`variant_id`, `merchant_size_label`, `is_available`, `matched`, `mismatched_fields_json`, `rank_order`).
5. **`fit_evaluation_cases`** & **`fit_evaluation_runs`**: curated labelled ground-truth cases and reproducible run metrics.

## Invalidation Triggers

Prior snapshots are marked `is_valid = False` with `invalidation_reason` & `invalidated_at` when:
- Shopper updates/deletes measurements, preferences, or consent (`FitProfileRepository.invalidate_fit_recommendations`)
- Size chart creates a new revision > `1` (`SizeChartService` → `FitRecommendationRepository.invalidate_for_chart`)
- Product/offer status or stock invalidation is invoked (`invalidate_for_product`, `invalidate_for_user`)
