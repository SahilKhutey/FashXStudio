# Fashion Image Embedding Subsystem Test Plan

## 1. Test Strategy & Traceability
The test suite validates correctness across all 24 acceptance criteria (EMB-001 through EMB-024) across model adapters, image preprocessing, vector validation, database persistence, nearest-neighbor retrieval, batch processing, and permission enforcement.

---

## 2. Test Matrix (EMB-001 through EMB-024)

| Test ID | Category | Description | Verification Method |
| :--- | :--- | :--- | :--- |
| **EMB-001** | Architecture | Approved model registry contains OpenCLIP ViT-B/32 | Unit test checking registry metadata |
| **EMB-002** | Adapter | Adapter implements `ImageEmbeddingAdapter` protocol | Runtime Protocol assertion |
| **EMB-003** | Dimensionality | Generated vectors have exactly 512 dimensions | Length verification on test image |
| **EMB-004** | Normalization | Generated vectors are L2-normalized ($\|v\|_2 = 1.0 \pm 10^{-5}$) | Mathematical norm check |
| **EMB-005** | Numerical Validity | Rejects vectors containing NaN or Inf values | Validation unit test with poisoned vectors |
| **EMB-006** | Zero Norm Reject | Rejects zero-norm vectors | Validation unit test with all-zero vector |
| **EMB-007** | Determinism | Repeated embeddings of identical image yield identical vectors | Deterministic hash/tolerance comparison |
| **EMB-008** | Preprocessing Bounds | Rejects images smaller than $100 \times 100$ or exceeding $4096 \times 4096$ | Preprocessor boundary test |
| **EMB-009** | EXIF Normalization | Auto-orients images with EXIF orientation metadata | Preprocessor test with rotated fixture |
| **EMB-010** | Aspect Preservation | Preserves aspect ratio with center padding on non-square images | Canvas dimensions & padding verification |
| **EMB-011** | Color Space | Converts grayscale and RGBA images to 3-channel RGB | Color space transform test |
| **EMB-012** | Corrupt File Safety | Fails safely when provided malformed or truncated image bytes | Exception handling unit test |
| **EMB-013** | Database Persistence | Persists embedding vector in `product_image_embeddings` table | Database insert & query test |
| **EMB-014** | Uniqueness Constraint | Enforces unique `(image_asset_id, model_id, model_version)` | Database constraint test |
| **EMB-015** | Permission Enforcement | Skips embedding when `IMAGE_AI_PROCESS` permission is missing | Security service mock test |
| **EMB-016** | Content Hash Match | Verifies `image_sha256` integrity against image asset | Hash comparison check |
| **EMB-017** | Nearest Neighbor | Cosine retrieval returns closest visual match as top result | Fixture vector nearest neighbor test |
| **EMB-018** | Visibility Filtering | Nearest neighbor excludes suspended or takedown-flagged assets | Retrieval filter query test |
| **EMB-019** | Model Migration | Blue/green migration allows dual-model coexistence and cutover | Migration orchestrator test |
| **EMB-020** | Canary Rollback | Canary rollback successfully reverts `is_active` to previous model | Rollback test |
| **EMB-021** | Batch Processing | Batched embedding preserves index ordering and completeness | Batch worker test |
| **EMB-022** | Retry Logic | Transient failures trigger retry with exponential backoff | Retry job test |
| **EMB-023** | Dead Letter Queue | Permanent failures record error trace in `embedding_jobs` | Failure recording test |
| **EMB-024** | Backward Compatibility | Legacy `FakeEmbedder` and `ImageTextEmbedder` imports succeed | Regression import check |
