# Phase 07.7 Repository Audit & Gap Analysis

## 1. Audit Scope & Objectives

This audit evaluates existing VTO execution, permission verification, and quality assessment components in FashXStudio to establish the foundation for **Phase 07.7 — VTO Quality Evaluation**.

The target requirements:
1. Controlled dataset governance: Explicit consent for AI processing, human review, and retention.
2. Production pipeline reuse: Evaluation must execute through the authentic VTO job pipeline (not a backdoor provider call).
3. Frozen configuration tracking: Snapshotting provider, model, preprocessing, prompt, and policy versions.
4. Multidimensional quality assessment: Independent human ratings across 6 dimensions plus automated image metrics.
5. Deterministic category gates: Gatekeeping garment categories into `APPROVED_LIMITED`, `NEEDS_IMPROVEMENT`, or `BLOCKED`.

---

## 2. Existing Baseline Code Assessment

### 2.1 Quality Evaluation
- **Existing File**: `backend/fashx/tryon/evaluation.py`
  - Defines `HumanVisualRating` with 5-point visual accuracy scale and simple issue tags (`unnatural_fit`, `garment_distorted`, etc.).
  - **Gaps Identified**:
    - Lacks multi-dimensional rubric (garment preservation, body alignment, artifacts, identity preservation, non-misleading score).
    - No multi-reviewer agreement calculation (weighted kappa / Krippendorff's alpha).
    - No automated image metrics (SSIM, CIEDE2000 color delta).
    - No category gate decision engine.

### 2.2 Dataset & Manifest Infrastructure
- **Existing Logic**:
  - `UserPhoto` in `database/models/identity.py` and `GarmentImage` in `database/models/catalog.py`.
  - **Gaps Identified**:
    - No dedicated evaluation dataset manifest entity or JSONL schema.
    - No participant pseudonymization mapping.
    - No evaluation-specific consent verification linking an image pair to permitted AI processing and human review.

### 2.3 Job Execution & Version Tracking
- **Existing Models**: `TryOnJob`, `TryOnProviderAttempt` in `database/models/tryon.py`.
  - Tracks `provider`, `model_version`, `request_hash`, and state machine transitions.
  - **Gaps Identified**:
    - No `tryon_evaluation_runs` entity capturing frozen configuration snapshots.
    - No linkage between evaluation dataset pairs and durable execution items.
    - No automated calculation of P95 latency and job success rates per garment category.

---

## 3. Architecture & Implementation Plan

| Component | Target Location | Description |
|---|---|---|
| **Contracts** | `backend/fashx/tryon/evaluation/contracts.py` | Pydantic models for evaluation pairs, dataset manifests, and run configurations. |
| **Runner** | `backend/fashx/tryon/evaluation/runner.py` | Orchestrates pair evaluation through authentic VTO service, enforcing Phase 07.6 budget limits. |
| **Ratings** | `backend/fashx/tryon/evaluation/ratings.py` | 6-dimension rubric, weighted scoring, reviewer agreement, and critical issue hard-fails. |
| **Category Gate** | `backend/fashx/tryon/evaluation/category_gate.py` | Threshold analysis, category state machine (`APPROVED_LIMITED`, `BLOCKED`, `NEEDS_IMPROVEMENT`). |
| **Image Metrics** | `backend/fashx/tryon/evaluation/image_metrics.py` | SSIM and CIEDE2000 color delta analysis on aligned garment regions. |
| **Database Schema** | `database/models/tryon.py` | Tables: `tryon_evaluation_datasets`, `tryon_evaluation_runs`, `tryon_evaluation_items`, `tryon_evaluation_ratings`, `tryon_evaluation_category_gates`. |
| **Migration** | `database/migrations/versions/0054_add_tryon_quality_evaluation.py` | Alembic migration for evaluation entities. |
