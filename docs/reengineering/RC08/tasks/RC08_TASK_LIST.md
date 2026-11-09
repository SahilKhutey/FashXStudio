# RC08 Execution Task List

## RC08.0 — Baseline and Governance
- [x] Record exact main SHA (`9e555dadec2a9d85b21bcfdbb95854f3ab17d214`)
- [x] Verify RC06 and RC07 merged commits in history
- [x] Create branch `recovery/rc08-staging-pilot-readiness` and push to origin
- [x] Run baseline mobile test suite (22 suites, 165 tests passed)
- [x] Create RC08 documentation scaffold (`00` through `17` and task list)
- [ ] Initialize staging deployment workflow

## RC08.1 — Environment and Configuration Management
- [x] Implement `ReleaseConfig` dataclass and validation logic (`backend/fashx/core/release_config.py`)
- [x] Integrate release validation into `backend/fashx/core/settings.py`
- [x] Add comprehensive release configuration unit tests (`tests/unit/test_rc08_release_config.py`)
- [ ] Configure staging environment variables and secret injection
- [ ] Verify production-safe feature flags

## RC08.2 — Authentication and Security Hardening
- [ ] Connect real Supabase staging authentication (JWKS)
- [ ] Verify dev token gate is strictly disabled in release builds
- [ ] Test cross-user isolation across wardrobe, try-on artifacts, and user profiles
- [ ] Verify rate limiting on auth, upload, and try-on endpoints
- [ ] Audit CORS origins and security headers

## RC08.3 — Database and Data Reliability
- [ ] Provision staging PostgreSQL 16 with pgvector
- [ ] Verify migration heads and clean upgrade execution
- [ ] Run database integration tests with Postgres service
- [ ] Test connection pool resilience and recovery under load

## RC08.4 — Object Storage, Privacy and Erasure
- [ ] Provision private staging S3/R2 bucket with public access block
- [ ] Verify pre-signed URL generation and expiry
- [ ] Test dual-layer account erasure (SQL + Object Storage)
- [ ] Verify retry mechanism for failed object deletions

## RC08.5 — AI and Integration Readiness
- [ ] Verify catalog source clearance and image rights
- [ ] Reconcile status documentation regarding FashionCLIP vs. test embeddings
- [ ] Execute real VTO inference test with consented test images
- [ ] Validate budget and daily rate caps

## RC08.6 — CI/CD Automation
- [ ] Add staging deployment workflow skeleton (`.github/workflows/rc08-staging.yml`)
- [ ] Ensure immutable image build and vulnerability scanning
- [ ] Validate deployment smoke testing and rollback runbooks

## RC08.7 — Observability and Monitoring
- [ ] Verify structured JSON logging with correlation IDs
- [ ] Define Prometheus metrics for API, queue, and VTO durations
- [ ] Configure alert thresholds for 5xx errors and latency spikes

## RC08.8 — Backup and Disaster Recovery
- [ ] Define backup schedules and WAL archiving
- [ ] Execute isolated restore drill
- [ ] Verify data integrity and measure actual RTO/RPO

## RC08.9 — Mobile Release and Device QA
- [ ] Build installable Android APK
- [ ] Execute physical Android device test matrix
- [ ] Verify camera capture, upload, polling, and network interruption handling

## RC08.10 — Legal and Partner Readiness
- [ ] Review privacy policy and consent wording under DPDP Act
- [ ] Document retailer permissions and affiliate program terms
- [ ] Execute VTO vendor Data Processing Addendum (DPA)

## RC08.11 — Controlled Pilot Operations
- [ ] Define participant consent and support process
- [ ] Execute founder-led closed test (5-10 users)
- [ ] Roll out limited closed pilot (20-40 participants)
- [ ] Monitor pilot stop rules and user feedback

## RC08.12 — Release Gate Decisions
- [ ] Review G1–G6 gate criteria
- [ ] Compile real runtime evidence register
- [ ] Human founder GO / NO-GO sign-off
