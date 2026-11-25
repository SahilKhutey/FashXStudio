# Evaluation Integration: Feedback to Phase 07.7

> **Connecting shopper feedback to benchmark regression testing and category release gates.**

## 1. Feedback-to-Evaluation Pipeline
When a shopper complaint is triaged and marked as `CONFIRMED`:
1. If `include_in_quality_review` is enabled, the feedback service registers an evaluation candidate referencing the exact inputs:
   - Shopper asset ID
   - Merchant garment image asset ID
   - Provider name, model version, and pipeline configuration
   - Feedback reason and confirmed root cause
2. The item is queued for inclusion in the frozen benchmark dataset (`datasets/vto/manifest.v1.jsonl`).

## 2. Severity Classification & Category Impact
- **CRITICAL**: Materially misleading output, complete identity distortion, or severe nudity/safety failure.
  - *Action*: Immediate triage, risk assessment, and potential category suspension via `TryOnEvaluationCategoryGate`.
- **HIGH**: Major garment distortion or loss of prominent pattern.
  - *Action*: Escalated review and automatic regression test case addition.
- **MEDIUM / LOW**: Visible minor artifacts or minor alignment imperfection.
  - *Action*: Aggregate quality trend tracking.
