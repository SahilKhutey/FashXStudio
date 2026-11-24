# Phase 07.3 — VTO Input Image Validation

## Objective
Establish a mandatory validation gate for shopper reference photographs and merchant garment images before submission to a Virtual Try-On inference provider.

## Scope
### Shopper Image
- Verify active third-party VTO consent (`THIRD_PARTY_VTO_PROCESSING` / `body_photo`).
- Verify asset ownership and private storage access (anti-enumeration).
- Validate file format (JPEG, PNG, WebP), dimensions, resolution, orientation, and integrity.
- Assess person visibility and category-specific body regions.
- Detect or flag unsuitable poses and occlusion.
- Return actionable upload guidance.
- Block unsuitable images from provider submission.

### Garment Image
- Verify merchant image-use and VTO processing permissions (`IMAGE_AI_PROCESS`, `VTO_PROCESS`).
- Verify product, offer, and image status (active, not delisted or in takedown).
- Verify product-image association.
- Validate image integrity, resolution, and dimensions.
- Assess garment visibility, cropping, and background suitability.
- Reject unsupported garment categories.
- Record exact product and image versions.

## Required Outcomes
- `PASSED`: All mandatory checks passed; provider submission allowed.
- `PASSED_WITH_WARNINGS`: Mandatory checks passed; non-blocking warnings present; allowed by policy.
- `NEEDS_REVIEW`: Automated assessment is uncertain; blocked pending resolution.
- `REJECTED`: Mandatory check failed; blocked.
- `EXPIRED`: Consent or authorization is no longer valid; blocked.
- `ERROR`: Validation infrastructure failed; blocked.

## Security Requirements
1. All ownership and authorization checks are server-side.
2. Client-provided permission claims and storage URLs are never trusted.
3. Required consent and merchant permissions are rechecked immediately before provider submission (time-of-use recheck).
4. A failed or uncertain validation never results in provider submission.
5. Image bytes, base64 data, and private storage URLs are never logged.
6. Validation evidence and exact image versions are durably auditable.
7. Failed images are never silently replaced by another photograph.

## Implementation Status
🟢 IMPLEMENTED — Architecture, validators, models, migrations, and test suite implemented on branch `feat/phase04.5-photo-upload`.

## Test Status
🟢 UNIT_VERIFIED — 31 unit tests covering technical inspection, shopper validation, garment validation, combined orchestration, and time-of-use guards passing.
🟡 STAGING_ACCEPTANCE — Staging live verification pending staging environment deployment.
