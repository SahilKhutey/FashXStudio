# FashXStudio — Phase 01.2 End-to-End Test Plan & Verification Register

**Document ID:** `FASHX-TEST-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.2 — Quality Assurance & Journey Verification Contract`  

---

## 1. Test Strategy Overview

Verification for the complete user journey operates across four tiers:
1. **Unit Tests:** Individual validation functions, permission gates, state machine transition guards, and event serialization schemas.
2. **Integration Tests:** FastAPI router to PostgreSQL persistence, Celery background job queuing, S3-compatible asset upload/download, and provider adapter mocks.
3. **End-to-End (E2E) Journey Tests:** Synthetic headless journey simulation from merchant onboarding through shopper outbound redirect.
4. **Security & Governance Tests:** Strict tenant boundary checks, DPDP consent enforcement, IDOR prevention, and URL allowlist verification.

---

## 2. Complete Journey Test-Case Register (JNY-001 – JNY-025)

| Test ID | Journey Scenario | Input Condition | Expected System Behavior | Test Level |
| :--- | :--- | :--- | :--- | :--- |
| **JNY-001** | Merchant Registration | Valid business name, email, phone, password | Merchant record created in `pending_verification` state. | Unit / API |
| **JNY-002** | Unverified Publication Attempt | Merchant attempts to publish before verification approval | Returns `HTTP 403 FORBIDDEN` (`MERCHANT_NOT_VERIFIED`). | Integration |
| **JNY-003** | Missing Image Rights | Merchant imports catalog without granting `MERCH_IMAGE_VTO` | Product imports cleanly but `vto_eligibility_status` is locked `INELIGIBLE`. | Integration |
| **JNY-004** | Valid Product Import | Valid CSV/JSON feed with title, SKU, price, images | Products ingested into `Validating` state with normalization. | Integration |
| **JNY-005** | Missing Required Fields | Ingested item lacks size or brand | Item routed to `Needs Review` state with actionable error flags. | Unit / Service |
| **JNY-006** | Invalid Garment Image | Product image resolution $< 400 \times 400$ px | Image rejected; product marked `VTO_INELIGIBLE`. | Unit / Service |
| **JNY-007** | Product Publication Approval | Validated product with active merchant agreement | Product promoted to `Published`; visible in discovery feed. | Integration |
| **JNY-008** | Shopper Registration & Auth | New email submitted; valid OTP entered | Session JWT issued; user identity record created. | Integration |
| **JNY-009** | Declining VTO Consent | Shopper declines `vto_photo_processing` in consent modal | Shopper can browse products; "Try it on" button is disabled. | E2E / Mobile |
| **JNY-010** | Partial Profile Creation | Shopper submits only height and usual size, skips weight | Profile saved; completion percentage calculates accurately. | Unit / API |
| **JNY-011** | Open Published Product | Shopper requests `GET /api/v1/products/{id}` | Returns canonical product details with correct merchant attribution. | Integration |
| **JNY-012** | Access Unpublished Product | Shopper attempts to fetch product in `Needs Review` state | Returns `HTTP 404 NOT_FOUND`; unpublished SKUs never leaked. | Security |
| **JNY-013** | Valid Photo Upload | Shopper uploads clear, single-person standing portrait | Asset uploaded to private S3; validation passes with confidence $\ge 0.85$.| Integration |
| **JNY-014** | Multi-Person Photo Upload | Shopper uploads group photograph | Validation fails with `MULTIPLE_PEOPLE_DETECTED` and retake guidance. | Unit / Service |
| **JNY-015** | Submit VTO Job | Valid product ID, asset ID, unique idempotency key | Exactly one VTO job enqueued; returns `status: queued`. | Integration |
| **JNY-016** | Duplicate Submission Guard | Client retries `POST /vto/jobs` with same idempotency key | Returns existing job without enqueuing duplicate background task. | Integration |
| **JNY-017** | GPU Provider Timeout | GPU inference worker exceeds 30-second deadline | Job safely transitions to `failed` (`PROVIDER_TIMEOUT`); retry permitted.| Integration |
| **JNY-018** | Recoverable Job Retry | Shopper clicks retry on timeout | New attempt dispatched under same logical job context. | Integration |
| **JNY-019** | Mid-Flight Perm Revocation| Merchant revokes image rights while job is processing | Result storage blocked; job marked `failed` with permission error. | Security |
| **JNY-020** | Save Completed Result | Shopper clicks "Save Look" on completed result | `SavedLook` record created linking result, product, and user. | Integration |
| **JNY-021** | Outbound Handoff Click | Shopper clicks "Buy at Merchant" | Outbound click logged; cryptographically signed merchant URL returned. | Integration |
| **JNY-022** | Cross-Tenant Analytics Guard| Merchant A requests metrics for Merchant B | Returns `HTTP 403 FORBIDDEN`; data strictly filtered by tenant ID. | Security |
| **JNY-023** | IDOR Asset Access Guard | User A requests presigned URL for User B's photo | Returns `HTTP 403 FORBIDDEN`; asset ownership strictly verified. | Security |
| **JNY-024** | Saved Look Deletion | Shopper deletes saved look from wardrobe | Look marked inactive; orphaned temporary assets scheduled for purge. | Integration |
| **JNY-025** | Malicious Redirect Block | Product record contains unapproved external domain | Redirection blocked with `HTTP 400 INVALID_DESTINATION`. | Security |

---

## 3. Negative & Edge-Case Failure Verification

The test harness must verify the following critical edge cases:
1. **Network Disconnection During Upload:** Client disconnects at 85% image upload; backend drops incomplete multipart parts; no orphaned DB entity created.
2. **Worker Crash Recovery:** Worker process terminated (`kill -9`) mid-inference; Celery/Redis re-queues task or marks job `failed` after visibility timeout expires.
3. **Stale Price at Handoff:** Product price changed on merchant site since last sync; FashXStudio displays freshness timestamp and disclaims final checkout price.
4. **Consent Withdrawal Cascades:** User revokes `vto_photo_processing`; active queued jobs for that user are immediately purged from Redis.
