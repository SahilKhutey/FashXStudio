# Dev Log: Phase 04.5 — Photo Upload and Validation Subsystem

- **Date:** 2026-11-17
- **Branch:** `feat/phase04.5-photo-upload`
- **Component:** Private Object Storage, Presigned Ingestion, Quarantine Validation, Metadata Stripping, WebP Normalization, Ephemeral Access URLs, and Mobile Client

---

## 1. Context & Objectives
Phase 04.5 implements a secure, private, validated photo-upload pipeline for FashXStudio, allowing shoppers to upload personal photos for approved profile or virtual try-on workflows without exposing the original image publicly or accepting unsafe files.

Key Invariants:
1. **Privacy-Sensitive Subsystem**: A personal photo is classified as private user media and biometric-adjacent data. Uploading does not automatically authorize third-party processing; processing requires separate, decoupled shopper consent.
2. **Zero Public S3 Buckets**: Public read access is completely blocked on all buckets.
3. **Quarantine Isolation**: Ingested files land in isolated quarantine prefixes (`temporary/uploads/...`) and are never read by try-on engines until verified, stripped, and normalized.
4. **Deterministic Server Keys**: Key generation is strictly server-side (`temporary/uploads/{env}/{user_id}/{upload_id}/original` and `users/{user_id}/images/{image_id}/original.webp`). Client filenames are metadata only.
5. **Multi-Stage Validation**: Magic byte container detection, declared MIME matching, strict Pillow bounded decoding (`MAX_IMAGE_PIXELS = 20_000_000`, dimensions $\le 4096\text{ px}$, size 10 KB to 10 MB), animated image rejection, orientation transpose, EXIF/GPS scrubbing, and fresh WebP raster normalization.
6. **Ephemeral Read Access**: Access is granted only via short-lived pre-signed GET URLs (60-second TTL) guarded by ownership checks. Non-owner requests return 404 Not Found to prevent enumeration.
7. **Rate Limiting & Concurrency**: Max 5 upload intents per user per 15 minutes; max 3 concurrent pending uploads; max 100 MB aggregate storage quota.

---

## 2. Engineering Changes

### 2.1 Database Models & Alembic Migration
- Created declarative models in `database/models/media.py`:
  - `UserMedia`: Stores validated user assets with dimensions, normalized WebP MIME type, size, SHA-256 checksums, and status (`AVAILABLE`, `DELETION_PENDING`, `DELETED`, `QUARANTINED`).
  - `MediaUpload`: Manages upload intent lifecycle, presigned PUT URL expiry, quarantine keys, and status (`PENDING_UPLOAD`, `VALIDATING`, `AVAILABLE`, `REJECTED`, `EXPIRED`, `CANCELLED`).
- Generated Alembic migration `0037_add_user_media_and_uploads.py` with foreign keys to `users.id` (cascade delete), check constraints, and performance indexes.
- Registered `user_media` and `media_uploads` in `backend/fashx/application/erasure.py` under `BIOMETRIC_TABLES` and added storage key collection to ensure full GDPR/DPDP user erasure compliance.

### 2.2 Core Media Validation & Service Engine
- Implemented `backend/fashx/media/keys.py`: Secure generation of quarantine keys and final private keys.
- Implemented `backend/fashx/media/validation.py`:
  - `detect_magic_format`: Inspects leading bytes for JPEG (`FF D8 FF`), PNG (`89 50 4E 47 0D 0A 1A 0A`), and WebP (`RIFF...WEBP`).
  - `validate_declared_mime`: Prevents MIME type spoofing.
  - `validate_image`: Executes bounded Pillow decoding, rejects animated/multi-frame media, transposes EXIF orientation, strips all metadata, and encodes fresh WebP rasters.
- Implemented `backend/fashx/media/repository.py`: Async queries for quota enforcement, rate limiting counts, pending concurrency counts, and status transitions.
- Implemented `backend/fashx/media/service.py`: `MediaUploadService` orchestrating intent initiation, quarantine validation, WebP promotion, metadata retrieval, expiring access URLs, and deletion.
- Implemented `backend/fashx/media/errors.py`: Domain exceptions mapped to RFC 7807 problem details and FashX error envelopes.

### 2.3 FastAPI Router & Dependencies
- Implemented `backend/fashx/media/router.py`:
  - `POST /api/v1/media/uploads`: Initiate upload intent and return presigned PUT URL.
  - `GET /api/v1/media/uploads/{upload_id}`: Poll upload validation status.
  - `POST /api/v1/media/uploads/{upload_id}/complete`: Trigger server verification and raster promotion.
  - `GET /api/v1/media/{image_id}`: Retrieve validated image metadata.
  - `POST /api/v1/media/{image_id}/access-url`: Generate 60-second presigned download URL.
  - `DELETE /api/v1/media/{image_id}`: Request immediate access revocation and object erasure.
- Mounted router in `backend/fashx/main.py` with `get_principal` authentication and registered `media_error_handler`.
- Added dev/test PUT upload route in `backend/fashx/main.py` to enable end-to-end local presigned URL uploads.

### 2.4 Mobile Client Implementation
- Implemented in `mobile/src/features/media/`:
  - `types/media.types.ts`: Comprehensive interfaces for upload requests, responses, metadata, and local photo selections.
  - `services/mediaApi.ts`: Type-safe API client communicating with backend media endpoints.
  - `services/uploadService.ts`: Local client-side pre-validation, streaming PUT binary upload, and validation polling.
  - `hooks/usePhotoUpload.ts`: Custom hook managing camera/library selection, pre-checks, binary transmission, and progress state.
  - `components/PhotoPicker.tsx`: UI component with thumbnail preview, size/dimension badges, error banners, and progress indicators.
  - `screens/PhotoUploadScreen.tsx`: Full-screen workflow featuring privacy & security disclosure cards and purpose selection.
  - `index.ts`: Unified module exports.

### 2.5 Documentation Deliverables
- Created comprehensive subsystem documentation in `docs/media/`:
  - `PHOTO_UPLOAD_ARCHITECTURE.md`
  - `PHOTO_UPLOAD_API.md`
  - `IMAGE_FORMAT_POLICY.md`
  - `IMAGE_SIZE_AND_DIMENSION_LIMITS.md`
  - `MEDIA_STORAGE_KEY_POLICY.md`
  - `MEDIA_DELETION_AND_RETENTION.md`

---

## 3. Verification & Test Execution
- **Unit Validation Tests (`tests/media/test_validation.py`)**: 12 tests passed (magic bytes, MIME check, dimension bounds, size boundaries, corruption handling, EXIF stripping, animated WebP rejection).
- **API Integration Tests (`tests/media/test_media_api.py`)**: 6 tests passed (unauthenticated 401s, 201 intent initiation, 429 concurrency and rate limit enforcement, end-to-end presigned PUT upload + complete workflow, cross-user 404 isolation, and deletion lifecycle).
- **Mobile Tests (`mobile/__tests__/photo_upload.test.ts`)**: 9 tests passed; full test suite (23 suites, 174 tests) passed.
- **Mobile TypeScript Typecheck**: Clean (`tsc --noEmit` exited code 0).
- **Python Linting & Typing**: `ruff check .` passed with 0 errors; `mypy backend/fashx/media` passed with 0 issues.
- **Secrets Audit**: `gitleaks detect --redact -v --exit-code=2` scanned 328 commits and confirmed 0 leaks.
- **Docs Lint**: `python scripts/docs_lint.py` passed with `docs lint ok`.
