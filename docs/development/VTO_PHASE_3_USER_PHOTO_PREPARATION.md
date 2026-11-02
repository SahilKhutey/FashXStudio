# VTO Phase 3 — User Photo Acquisition, Consent, Validation, and Person-Image Preparation

**Project:** FashXStudio
**Phase:** VTO-3
**Status:** Implementation specification
**Objective:** Ingest user portrait photos under explicit consent, validate quality and suitability, normalize dimensions and orientation, perform person detection, and persist private prepared person assets for virtual try-on inference.

## 1. Scope
Phase 3 builds the secure pipeline that accepts a user photo, verifies that the user has explicitly consented to virtual try-on processing, validates image quality and suitability, and stores a prepared person image for the VTO inference service.

Included:
- Explicit consent verification for `body_photo` (GDPR Rule I07)
- Age verification check (`is_18_or_older IS TRUE`)
- Consent policy version validation against active platform settings
- User photo payload sanitization and metadata/EXIF stripping
- EXIF camera orientation normalization (`ImageOps.exif_transpose`)
- RGB color mode normalization (compositing alpha transparency onto white)
- Resolution validation (minimum 256x320, recommended >= 512x512)
- Max dimension scaling (LANCZOS downsampling preserving aspect ratio, max side <= 1536px)
- Portrait framing heuristics and aspect ratio evaluation (target 3:4 portrait)
- Exposure heuristics (mean luminance bound [40.0, 220.0]) and contrast validation (std dev >= 15.0)
- JPEG normalization (quality 92) and SHA-256 byte hashing
- Pluggable `PersonDetector` protocol with `HeuristicPersonDetector` and `MockPersonDetector`
- Try-on readiness evaluation (`ready_for_tryon` flag and detailed `quality_reasons`)
- Private object storage upload (`u/{user_id}/photos/{photo_id}.jpg` / `media_key(user_id, "reference_photo", photo_id)`)
- Compensating transaction: purge storage asset if database commit fails
- Database metadata persistence across `user_photos` and `media_objects`

Excluded:
- AI virtual try-on inference execution (Phases 4/5)
- Model fine-tuning or training on user photos
- Biometric identification, facial recognition, or claiming exact bodily dimensions
- Retailer catalog image preparation (handled in Phase 2)
- Multi-garment styling composition

## 2. Processing and Security Rules
1. **Consent Gate:** Virtual try-on processing requires an active, unrevoked consent record for `body_photo`.
2. **Adult Verification:** In accordance with schema check constraint `ck_consent_granted_requires_adult`, photos are rejected if the user is not verified as 18 or older.
3. **Consent Version:** Consent records must match the current active platform `consent_version` (default `"2026.1"`).
4. **Orientation Correction:** Mobile camera uploads often contain EXIF orientation tags without pixel rotation. The pipeline normalizes orientation before measuring framing or contrast.
5. **Private Storage:** Stored user assets are private. Capability URLs are short-lived signed URLs (Rule I06).
6. **Compensating Rollback:** If database transaction fails after storage upload, the orphaned storage object is immediately deleted.
7. **Fail-Closed Detector:** The `PersonDetector` validates that exactly 1 person is present in the frame. If 0 persons or multiple people are detected, `ready_for_tryon` is set to `False` with the corresponding quality reason.
8. **No Model Training:** User photos are used exclusively for authorized try-on inference requests and are never used for foundation model training or unauthorized third-party sharing.

## 3. Storage and Database Layout
Storage key pattern:
`u/{user_id}/photos/{photo_id}.jpg` (via `media_key(user_id, "reference_photo", photo_id)`)

Database `UserPhoto` fields populated:
- `user_id`: Owning user UUID
- `photo_type`: "tryon_reference"
- `storage_key`: Private object storage key
- `status`: "accepted" or "rejected"
- `content_sha256`: SHA-256 hex digest of normalized JPEG bytes
- `width`: Prepared image width in pixels
- `height`: Prepared image height in pixels
- `image_format`: "JPEG"
- `file_size_bytes`: Byte length of stored image
- `has_person`: Boolean indicating presence of 1 person
- `has_face`: Boolean indicating face detection
- `quality_score`: Composite quality score (0.0 to 1.0)
- `framing_score`: Aspect ratio portrait framing score (0.0 to 1.0)
- `pose_score`: Estimated pose suitability score
- `ready_for_tryon`: True only if all critical quality gates and person detection pass
- `quality_reasons`: List of strings explaining quality warnings or failure reasons
- `pose_provider`: Name of detection provider (e.g., "heuristic_detector", "mock_detector")
- `pose_provider_version`: Version string of detector

## 4. Key Components
- `backend/fashx/profile/images/detector.py`:
  - `PersonDetection`: Dataclass containing detection metrics.
  - `PersonDetector`: Protocol defining `detect(image_bytes: bytes) -> PersonDetection`.
  - `HeuristicPersonDetector`: Fast, lightweight heuristic analyzer for aspect ratio, luminance, and contrast.
  - `MockPersonDetector`: Deterministic detector for unit and integration testing.
  - `ConfiguredPersonDetector`: Proxy delegating to an injected or default detector backend.
- `backend/fashx/profile/images/prepare_photo.py`:
  - `PersonPhotoPreparer`: Normalizes, resizes, checks lighting/contrast, encodes JPEG, and evaluates try-on readiness.
  - `PreparedPhoto`: Dataclass holding normalized image bytes, SHA-256 hash, and quality metrics.
  - `PhotoPreparationError`: Domain exception with failure codes.
- `backend/fashx/profile/application/prepare_user_photo.py`:
  - `UserPhotoUploadService` / `PrepareUserPhotoUseCase`: Orchestrates consent checks, photo preparation, storage upload, compensating rollback, and DB persistence.
- `backend/fashx/profile/repositories/profile_repository.py`:
  - `UserPhotoRepository.create`: Persists photo records with full metadata columns.
  - `UserConsentRepository.has_valid_consent`: Validates consent granting, age check, and version match.
- `backend/fashx/profile/application/upload_photo.py`:
  - Upgraded to use `PersonPhotoPreparer` and populate full metadata while maintaining backward compatibility with legacy consumers.

## 5. Verification Checklist
- [x] EXIF orientation normalization verified.
- [x] RGB conversion with alpha transparency compositing on white background verified.
- [x] LANCZOS downsampling preserving aspect ratio for oversized images verified.
- [x] Resolution bounds (minimum 256x320) verified.
- [x] Framing, exposure, and contrast heuristics verified.
- [x] Person detection count (0, 1, >1) and `ready_for_tryon` flag verified.
- [x] Explicit consent requirement (`body_photo`) verified.
- [x] Minor / under-18 protection verified.
- [x] Consent version mismatch rejection verified.
- [x] Storage cleanup on DB persistence failure verified.
- [x] Database record persistence with SHA-256 content hash verified.
- [x] Route snapshot and backward compatibility verified.
