# Database Migrations: Phase 07.8

> **Schema migration, index strategy, and rollback procedures.**

## 1. Migration Specification
- **Revision ID**: `0055_add_vto_fit_separation_and_size_charts`
- **Revises**: `0054_add_tryon_quality_evaluation`

## 2. Schema Changes
1. **`tryon_feedback` additions**:
   - `reason_code` (`VARCHAR(64)`, nullable)
   - `details` (`TEXT`, nullable)
   - `include_in_quality_review` (`BOOLEAN`, default `false`)
   - `review_status` (`VARCHAR(32)`, default `'RECEIVED'`)
   - `visual_accuracy` made nullable to support direct complaint submissions.
2. **`fit_recommendations` table**:
   - Stores deterministic fit evaluation results, evidence provenance, and validity flags.
3. **`tryon_feedback_reviews` table**:
   - Stores reviewer triage decisions, root-cause classifications, and Phase 07.7 evaluation links.
4. **`merchant_verified_size_charts` table**:
   - Stores verified merchant size tables, explicit basis (`BODY` vs `GARMENT`), and freshness metadata.

## 3. Rollback Strategy
The migration defines a strict `downgrade()` function that drops newly created tables and indices and reverts added columns via `batch_alter_table`.
