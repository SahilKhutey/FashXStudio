# VTO Phase 9 — AI Quality Evaluation, Visual Accuracy & Feedback Learning

**Project:** FashXStudio  
**Phase:** VTO 9  
**Status:** Implementation specification  
**Scope:** Perceived visual realism evaluation, feedback ingestion, issue categorization, release quality gates  
**Prerequisite:** VTO Phase 8 — Wardrobe, Product Variants & Shopping Handoff  

---

## 1. Objective & Scope Boundary

Phase 9 establishes a systematic, measurable visual quality evaluation and user feedback learning architecture for FashXStudio's Virtual Try-On (VTO) pipeline.

### Core Objectives
1. **Perceived Realism Ingestion**: Capture user and evaluator ratings regarding visual realism, texture fidelity, and garment drape perception without conflating visual appearance with physical fit.
2. **Issue Tag Attribution**: Structure quality degradation into actionable categorization tags (`unnatural_fit`, `garment_distorted`, `color_inaccurate`, `blurry_artifacts`, `person_appearance_changed`, `wrong_garment`, `occlusion_error`).
3. **Evaluation Summary & Release Gate**: Provide reproducible benchmarking tools to evaluate model releases or provider transitions against human visual evaluations.
4. **Mobile Feedback Integration**: Decouple visual rating and issue chip selection from immediate mutation, submitting atomic feedback upon user confirmation.

### Scope Boundary & Safety Guarantees
- **Visual Realism vs Physical Sizing**: High visual fidelity does not prove that a garment fits the user's physical body measurements. Physical sizing calibration is handled separately via `FitFeedback` and brand sizing bias ledgers.
- **Privacy & Storage Security (Rule 7)**: Evaluation manifests reference anonymized sample identifiers and canonical garment metadata. Private user body photos, face crops, and signed storage URLs are strictly excluded from benchmark manifests.

---

## 2. Feedback Ingestion Architecture

### 2.1 Database Schema (`tryon_feedback`)
The `tryon_feedback` table persists user ratings and categorical issue diagnostics:

- `id`: UUID primary key.
- `user_id`: Foreign key to `users.id` (CASCADE delete on user erasure).
- `tryon_job_id`: Foreign key to `tryon_jobs.id` (CASCADE delete).
- `visual_accuracy`: Categorical realism perception (`very_inaccurate`, `inaccurate`, `neutral`, `accurate`, `very_accurate`).
- `purchase_confidence`: Optional integer rating from 1 to 5.
- `provider`: Provider recorded at job execution time (e.g., `mock`, `fashn_api`).
- `issue_tags`: JSON array of validated issue strings, defaulting to `[]`.
- `created_at`: UTC timestamp.
- Unique constraint: `uq_tryon_feedback_user_job (user_id, tryon_job_id)`.

Alembic migration `0032_tryon_feedback_issue_tags` adds the `issue_tags` JSON column with batch alteration support.

### 2.2 Domain Use Case (`SubmitTryOnFeedbackUseCase`)
The use case enforces strict validation and authorization gates:
1. **Visual Accuracy Gate**: Rejects unlisted values; must match `VALID_ACCURACIES`.
2. **Purchase Confidence Range**: Optional integer must fall between 1 and 5.
3. **Issue Tags Allowlist**: Every supplied tag must exist in `VALID_ISSUE_TAGS`:
   `{"unnatural_fit", "garment_distorted", "color_inaccurate", "blurry_artifacts", "person_appearance_changed", "wrong_garment", "occlusion_error"}`.
4. **Job Existence**: Validates `tryon_job_id` against `TryOnJob`; raises `NotFoundError` if missing.
5. **Ownership Check**: Rejects requests where `job.user_id != cmd.user_id` with `AuthorizationError`.
6. **Completion Check**: Requires `job.status == "completed"`; rejects incomplete or failed jobs.
7. **Idempotency Guarantee**: Looks up existing feedback via `TryOnFeedbackRepository.get_by_user_and_job`. If present, returns the existing record idempotently without duplicating database rows or throwing constraint errors.

### 2.3 API Router & Contract (`POST /feedback/tryon`)
- **Request Payload (`TryOnFeedbackRequest`)**:
  - `tryon_job_id: UUID` (required)
  - `visual_accuracy: VisualAccuracy` (required)
  - `purchase_confidence: int | None = Field(default=None, ge=1, le=5)` (optional)
  - `issue_tags: list[str] = Field(default_factory=list)` (optional)
  - `user_id: UUID | None = None` (optional)
- **Principal Authorization**: Derives the authenticated user ID from `principal.user_id`. If `request.user_id` is supplied, it must match the principal ID or a 403 Forbidden is returned.

---

## 3. Human Visual Evaluation Module

The evaluation engine in `backend/fashx/tryon/evaluation.py` defines the evaluation structures:

```python
@dataclass
class HumanVisualRating:
    sample_id: str
    visual_accuracy: str
    issue_tags: list[str] = field(default_factory=list)
    purchase_confidence: int | None = None
    rater_id: str | None = None
```

```python
@dataclass(frozen=True)
class VisualEvaluationSummary:
    total_samples: int
    acceptable_count: int
    acceptable_rate: float
    accuracy_counts: dict[str, int]
    issue_tag_counts: dict[str, int]
    mean_accuracy_score: float | None
    mean_purchase_confidence: float | None
```

The function `summarize_visual_ratings(ratings, acceptable_threshold="accurate")` computes release gate metrics:
- **Acceptable Count**: Count of samples meeting or exceeding the threshold (`accurate` = score 4, `very_accurate` = score 5).
- **Acceptable Rate**: Fraction of acceptable generations over total evaluated samples.
- **Accuracy Counts**: Distribution across all 5 discrete realism bins.
- **Issue Tag Counts**: Aggregated diagnostic occurrences across all evaluated items.
- **Mean Realism Score**: Numerical mean on 1–5 scale.
- **Mean Purchase Confidence**: Numerical mean on 1–5 scale for samples providing purchase confidence.

---

## 4. Mobile User Experience

Located in `mobile/app/tryon/[jobId].tsx` and `mobile/src/features/tryon/useTryOn.ts`:
1. **Interactive Rating (1–5 Stars)**: User taps a star to set their rating locally (`handleSelectRating`). Rating selection does not trigger an immediate network request.
2. **Issue Chips Multi-Selection**:
   - If rating $\le 3$, diagnostic chips are surfaced:
     - `Fit looks unnatural` (`unnatural_fit`)
     - `Garment distorted` (`garment_distorted`)
     - `Color inaccurate` (`color_inaccurate`)
     - `Blurry or artifacts` (`blurry_artifacts`)
     - `Person altered` (`person_appearance_changed`)
     - `Wrong garment` (`wrong_garment`)
     - `Occlusion error` (`occlusion_error`)
   - Chips can be independently toggled on and off.
3. **Explicit Submission**:
   - An explicit "Submit feedback" CTA appears once a rating is selected.
   - On tap, dispatches an atomic payload containing `rating`, `issueTags`, and `tryon_job_id`.
   - On success, displays `✓ Feedback submitted! Thank you.` and prevents repeated mutations.
