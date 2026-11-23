# Image Pipeline Architecture

## 1. Overview and Core Principle

The FashXStudio Product Image Pipeline provides a secure, permission-aware, and reproducible image ingestion, transformation, and takedown subsystem.

The non-negotiable core architectural invariant governing this phase is:

> **An image URL is not permission to download; permission to download is not permission to store; permission to display is not permission to process with AI; and permission to process is not automatically permission to create or retain a VTO derivative.**

```mermaid
flowchart TD
    A[Catalog Ingestion / Image Job] --> B{Preflight Permission Check}
    B -- Denied --> C[Reject: fail closed]
    B -- Allowed --> D[Safe Image Fetcher]
    D -- HTTPS / SSRF / Byte Limit --> E[Image Inspector]
    E -- MIME / Format / Decompression Bomb --> F{Valid Bytes?}
    F -- No --> G[Reject / Log Error]
    F -- Yes --> H[Quality Validator]
    H -- Display Profile & VTO Profile --> I[Image Hasher]
    I -- SHA-256 & dHash --> J{Duplicate Detection}
    J -- Same Product Duplicate --> K[Reuse Existing Asset]
    J -- Novel or Shared Stock --> L[Private Object Storage]
    L -- IMAGE_STORE Permitted --> M[Store Original Bytes]
    L -- IMAGE_STORE Prohibited --> N[Skip Original Storage]
    M --> O[Generate Display Derivatives]
    N --> O
    O -- WebP Thumbnail, Card, Detail --> P{AI / VTO Rights?}
    P -- Granted --> Q[Generate VTO Input PNG]
    P -- Denied --> R[Skip VTO Derivative]
    Q --> S[Persist Asset & Transformation Records]
    R --> S
```

---

## 2. Component Structure

| Component | Module | Responsibility |
| :--- | :--- | :--- |
| **`ProductImagePipeline`** | `backend/fashx/catalog/images/pipeline.py` | Orchestrates end-to-end flow, fail-closed rights checks, deduplication, and compensation cleanup. |
| **`ImagePermissionService`** | `backend/fashx/catalog/images/permissions.py` | Granular permission evaluation via `CatalogAuthorizationGuard`. |
| **`SafeImageFetcher`** | `backend/fashx/catalog/images/fetcher.py` | Enforces HTTPS, host allowlists, SSRF IP defense, DNS rebinding guards, streaming byte limits, and safe failure codes. |
| **`ImageInspector`** | `backend/fashx/catalog/images/inspector.py` | Validates magic bytes, decodes formats (JPEG, PNG, WebP), catches decompression bombs, checks dimensions (400–4096px), transposes EXIF orientation, strips metadata. |
| **`ImageQualityValidator`** | `backend/fashx/catalog/images/quality.py` | Evaluates display and VTO profiles (`PASS`, `REVIEW`, `REJECT`, `NOT_APPLICABLE`). |
| **`ImageHasher`** | `backend/fashx/catalog/images/hasher.py` | Computes SHA-256 for original, normalized, and derivative bytes, and perceptual difference hash (dHash). |
| **`ImageStorageService`** | `backend/fashx/catalog/images/storage_service.py` | Manages private object storage paths, signed URLs, and rollback cleanup. |
| **`ImageTransformationService`** | `backend/fashx/catalog/images/transformations.py` | Creates versioned WebP display derivatives and garment-preserving PNG VTO inputs. |
| **`ImageLifecycleService`** | `backend/fashx/catalog/images/lifecycle.py` | Orchestrates takedowns, immediate asset suspension, cascade object deletion, and retry tracking. |

---

## 3. Transactional Compensation & Failure Handling

If a database write fails after storage uploads have commenced, the pipeline catches the error, calls `storage.delete()` on all newly created keys, and reports `db_commit_failed`, preventing orphaned object accumulation in S3.
