# AI and Virtual Try-On (VTO) Image Permission Policy

**Workstream**: 5.1.7 — Artificial Intelligence and Virtual Try-On Permissions  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/authorization/`

---

## 1. Architectural Motivation
Modern virtual try-on pipelines and computer vision classifiers extract fine-grained geometric, texture, and model features from product imagery. Many brand agreements permit standard e-commerce display while strictly forbidding synthetic image modification, deep learning model training, or virtual try-on simulation.

Therefore, FashXStudio enforces a **strict, fail-closed separation** between display rights and AI/VTO processing rights.

---

## 2. Granular AI Scopes

### 2.1 `IMAGE_AI_PROCESS`
- **Definition**: Authority to pass original product imagery into computer vision models, including:
  - Deep learning garment segmentation (e.g., Segment Anything / SAM, UNet).
  - Feature extraction and neural embedding generation (e.g., CLIP, ViT).
  - Automated attribute classification (e.g., neckline, sleeve length, pattern recognition).
  - Keypoint and landmark estimation.
- **Enforcement**: Ingestion guard `guard_image_ai_process` evaluates source status and permission prior to dispatching any Celery AI inference job.

### 2.2 `VTO_PROCESS`
- **Definition**: Authority to utilize garment representations as inputs to virtual try-on diffusion models, warpers, and rendering pipelines combining shopper photos with garment assets.
- **Consent Precondition**: Even when `VTO_PROCESS` is granted by the merchant, VTO execution requires separate shopper biometric consent (Phase 04.4).
- **Prohibited without Explicit Grant**: An image authorized for catalog search display cannot be submitted to the VTO inference pipeline.

---

## 3. Processor Restrictions

A merchant may authorize AI processing strictly under specific processors (e.g. only self-hosted internal models, strictly forbidding third-party SaaS AI APIs like OpenAI, Midjourney, or external cloud vision vendors).

`CatalogSourcePermission.processor_restrictions` contains an allowlist of approved processor identifiers:
```json
["internal_segmenter_v1", "sam_vit_h_self_hosted"]
```
- If `processor_restrictions` is empty or contains `"*"`, any authorized internal processor is permitted.
- If `processor_restrictions` is populated, the execution engine validates that `context.processor_id` is an exact match.
- If a job requests `third_party_cloud_api` against a restricted permission, the engine immediately rejects execution with `DENY_PROCESSOR_NOT_PERMITTED`.

---

## 4. Verification Check
- Test coverage: `tests/catalog/test_permissions_and_evaluator.py::test_cat_perm_007_invariant_image_display_does_not_grant_ai_process` and `test_cat_perm_008_invariant_image_store_does_not_grant_vto_process`.
