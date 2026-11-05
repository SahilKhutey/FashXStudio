# RC08 — Baseline and Scope

## 1. Repository Baseline
- **Repository**: `SahilKhutey/FashXStudio`
- **Baseline Commit**: `9e555dadec2a9d85b21bcfdbb95854f3ab17d214` (`origin/main`)
- **Active Branch**: `recovery/rc08-staging-pilot-readiness`
- **Target Pull Request**: `recovery/rc08-staging-pilot-readiness` -> `main`
- **Recent Merges Confirmed**:
  - RC06 (Shopping, Retailer Offers & Purchase Handoff): PR #28 (`a9f28f3`)
  - RC07 (Real Catalog Enrichment & Personalization): PR #29 (`9e555da`)

## 2. In-Scope Boundaries
1. **Infrastructure & Staging Environments**:
   - Explicit environment separation (`development`, `staging`, `production`).
   - Release configuration validation via `ReleaseConfig` and fail-closed security invariants.
   - Immutable container packaging with Git commit SHA tagging.
2. **Authentication & Security Hardening**:
   - Production/Staging JWKS token validation using hosted identity provider (Supabase Auth).
   - Zero-trust access controls on sensitive resources (wardrobe, tryon artifacts, user profiles).
   - Rate limiting, strict CORS whitelisting, and SSRF upload guards.
   - Prohibiting mock authentication and mock try-on in production.
3. **Database & Persistence Reliability**:
   - Single clean migration head verification on PostgreSQL 16 + pgvector.
   - Connection pool resilience, query timeouts, and retry policies.
   - Automated backup configuration and verified restore drills.
4. **Object Storage, Privacy & Retention**:
   - Private bucket configuration for personal capture photos and VTO artifacts.
   - Time-limited signed URL generation (TTL ≤ 300s).
   - Dual-layer account deletion: transactional database purge + verified asynchronous object-store erasure.
5. **AI & Provider Reality Reconciliation**:
   - Reconciling documentation to accurately reflect mock vs. real inference state.
   - Pinned provider identifiers and budget limit guards.
   - Staging smoke verification against real providers where credentials are provisioned.
6. **Observability & Incident Operations**:
   - Structured JSON logging with trace context.
   - Metrics emission for request volume, error rates, latency, worker queue depth, and VTO durations.
   - Pilot SLO definitions and alert thresholds.
7. **Mobile Readiness & Physical Device QA**:
   - Physical Android device test matrix (camera capture, upload, polling, network drop recovery).
   - Standalone installable APK generation criteria.

## 3. Explicit Out-of-Scope Boundaries
- **FashX-Owned Payment Processing**: Direct payment gateway integration (Stripe, Razorpay) remains frozen; external retailer handoff (`/api/v1/commerce/buy-clicks`) is authoritative.
- **Unconsented Public Launch**: Open public app store release is out of scope; pilot operations are strictly restricted to consented closed cohorts (20–40 users max).
- **Simulated Compliance Claims**: No automated test shall be claimed as legal compliance with the Digital Personal Data Protection (DPDP) Act without qualified legal review.
