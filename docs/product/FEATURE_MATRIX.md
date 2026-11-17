# FashXStudio — Complete Feature Inventory & Priority Matrix

**Document ID:** `FASHX-FEAT-001`  
**Version:** `1.0 — Frozen Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.3 — Feature Classification & Priority Freeze`  

---

## 1. Subsystem Classification & Priority Table

This matrix classifies every platform capability into **P0 (Must Work)**, **P1 (Should Work)**, and **P2 (Later / Post-MVP)**, cross-referencing current repository evidence against live pilot readiness.

| Subsystem | P0 — Must Work (Pilot Blocker) | P1 — Should Work (Simplified/Manual) | P2 — Later (Post-MVP / Frozen) | Repository Status & Integration Gap |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | Registration, login, logout, JWT session management, password recovery, token expiration. | Social login (Google/Apple), magic links, SMS OTP. | Enterprise SSO, multi-factor auth, SAML federation. | 🟢 Code present in `fashx.security`; needs verification with production auth keys. |
| **Shopper Profile**| Basic body measurements (height, weight, usual size), fit preferences, DPDP consent capture. | Brand-specific size preferences, extended style quiz. | Automatic 3D body shape extraction, photo-based biometric estimation. | 🟢 Profile models present in `fashx.profile`; progressive UX flow pending. |
| **Catalog Ingestion**| 1 authorized merchant source (CSV/feed/API adapter), canonical schema normalization, basic validation. | Second catalog source, scheduled auto-sync, automated category mapping. | Broad multi-retailer scraping, crawler network, headless browser scrapers. | 🟢 Pipeline & validator present in `fashx.catalog`; live partner feed pending. |
| **Catalog Governance**| Source permission verification, image-use rights check, duplicate SKU detection, publication gates. | Merchant self-service error resolution portal, bulk review UI. | Automated copyright crawler, image trademark scanning. | 🟢 Permission entities & deduplication rules present; needs merchant UI wire-up. |
| **Discovery & Search**| Multi-brand feed, category navigation, keyword search, size/price filters, PDP with size chart modal. | Personalized vector ranking, trending drops, color-swatch filtering. | Multi-store visual search, cross-retailer price comparison. | 🟢 Fast retrieval & ranking code present; real user relevance unmeasured. |
| **Virtual Try-On** | Real provider-backed inference (FASHN), async Celery queue, idempotent job submission, progress tracking, result retrieval, error recovery. | Visual pose guidance, automated single-retry on blur, user-facing quality rating. | Custom fine-tuned diffusion model, self-hosted GPU cluster, multi-garment layering. | 🟢 Adapter & orchestration present in `fashx.tryon`; **P0 Blocker:** Live vendor credentials needed. |
| **Digital Wardrobe**| Save, retrieve, inspect, and delete try-on looks; price-snapshot tracking. | Custom collections, tags, favorites, try-on history timeline. | AI outfit generator, packing assistant, style calendar. | 🟢 Repositories present in `fashx.commerce_wardrobe`; mobile persistence verified. |
| **Merchant Platform**| Manual merchant onboarding by team, product-page handoff, basic catalog controls. | Self-service web dashboard, embeddable PDP widget, source sync status. | Full merchant marketplace portal, multi-brand billing settlement. | 🟡 Tenant code present in `fashx.b2b`; currently feature-flagged off for pilot. |
| **Analytics** | Universal event envelope, 28+ instrumented events, event deduplication, funnel aggregation. | Exportable merchant conversion summary report (CSV/PDF). | Real-time streaming analytics, predictive cohort churn models. | 🟢 Event infrastructure present in `fashx.analytics`; verified in tests. |
| **Feedback Engine** | Basic try-on quality score (1–5 stars), issue flagging modal. | Structured fit feedback ("runs small", "runs large"). | Closed-loop automated model re-ranking from feedback. | 🟢 Schemas present; mobile bottom-sheet integration pending. |
| **Privacy & Security**| Tenant isolation, private S3 buckets, presigned URLs, consent revocation, cryptographic erasure logging. | Self-service privacy center in mobile app. | Automated compliance reporting for external regulatory audits. | 🟢 DPDP models & tombstone mechanisms present in `fashx.security`. |
| **Infrastructure** | Dockerized FastAPI, Redis queue, Postgres 16 + pgvector, structured logs, request correlation IDs. | Staging deployment pipeline, basic uptime alerts. | Multi-region active-active deployment, autoscaling GPU nodes. | 🟡 Local docker-compose & CI workflows present; cloud staging pending. |
| **Mobile Experience**| Expo React Native app, 4-tab shell, photo camera/gallery capture, VTO result slider, error states. | Tablet optimization, advanced skeleton shimmer animations. | Native iOS/Android widgets, AR live camera mirror. | 🟢 21 Jest suites passing; physical device testing pending. |
| **Commerce Operations**| Validated outbound product redirect (`/outbound-clicks`) with signed affiliate tracking ID. | Affiliate network postback callback integration. | ❄️ **FROZEN:** Cart, checkout, payment gateway, inventory, shipping, returns. | ❄️ Frozen post-MVP code unmounted per ADR-0001. |

---

## 2. Concrete Acceptance Criteria for P0 Features

A feature is approved as **P0** only when it satisfies an unambiguous, testable acceptance condition:

### 1. Authentication & Security (P0-AUTH)
- **Criterion:** An unauthenticated user can register with a unique email/phone, verify access via OTP/token, receive an encrypted JWT access/refresh token pair, and terminate the session via logout.
- **Verification:** Expired tokens return `HTTP 401 UNAUTHORIZED`; tamper-evident signatures reject modified payloads.

### 2. Shopper Profile & DPDP Consent (P0-PROF)
- **Criterion:** Shopper can record consent decisions for individual purposes (`SHOP_PHOTO_VTO`, `SHOP_PROFILE_STYLE`). Revoking photo consent immediately blocks subsequent VTO requests without restricting product browsing.
- **Verification:** Consent records persist timestamp, policy version, and IP.

### 3. Authorized Catalog Feed (P0-CAT)
- **Criterion:** Exactly one live partner feed imports at least 50 valid upper-body apparel SKUs into the canonical schema.
- **Verification:** Missing required fields (SKU, title, image URL) route products to `Needs Review`; unauthorized images are rejected.

### 4. Product Publication & VTO Gate (P0-PUB)
- **Criterion:** Products enter the published discovery index only when merchant verification and image-use rights are active.
- **Verification:** Products with unverified image licenses are flagged `vto_eligibility_status = INELIGIBLE`.

### 5. Multi-Brand Discovery (P0-DISC)
- **Criterion:** Shoppers can query the feed via text search, filter by size and price range, and view responsive product cards with clear VTO availability indicators.
- **Verification:** Search latency p95 is $< 800$ms on indexed catalogs.

### 6. Real Provider Virtual Try-On (P0-VTO)
- **Criterion:** A valid shopper photo and authorized garment image submitted to `POST /api/v1/vto/jobs` generates a realistic diffusion try-on result via FASHN API.
- **Verification:** Inference output is stored in private S3; presigned URL expires after 1 hour; mock adapter is barred from staging/production.

### 7. Asynchronous Queue & Idempotency (P0-QUEUE)
- **Criterion:** Duplicate submissions with the same `Idempotency-Key` return the existing job record without re-enqueuing GPU workloads.
- **Verification:** Celery worker failure or timeout safely updates job status to `failed` with a user-actionable error code.

### 8. Digital Wardrobe & Saved Looks (P0-WARD)
- **Criterion:** Shoppers can save completed try-on results to their digital wardrobe and retrieve them across app restarts.
- **Verification:** Deleting a saved look purges the relational record and marks temporary generated assets for deletion.

### 9. Outbound Commerce Handoff (P0-COMM)
- **Criterion:** Tapping "Buy at Merchant" records an outbound click event, validates the destination domain against the merchant allowlist, and opens the official brand PDP.
- **Verification:** Malicious or unapproved external redirect URLs return `HTTP 400 INVALID_DESTINATION`.

### 10. Funnel Telemetry (P0-ANL)
- **Criterion:** Core shopper funnel events (`product_impression`, `product_clicked`, `vto_cta_clicked`, `vto_job_completed`, `merchant_handoff_clicked`) are logged with unique UUIDs and pseudonymous shopper IDs.
- **Verification:** Analytics queries return accurate aggregation partitioned by `merchant_id`.
