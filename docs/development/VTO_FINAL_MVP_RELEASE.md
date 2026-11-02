# FashXStudio — Virtual Try-On Final MVP Release

**Phase:** Final / Phase 12 of 12  
**Release:** VTO MVP 1.0  
**Status:** Release specification — evidence pending  
**Target Environment:** AWS Mumbai (`ap-south-1`)  
**Prerequisites:** VTO Phases 0 through 11  

---

## 1. Purpose

This document defines the final integration, validation, and release requirements for the FashXStudio Virtual Try-On (VTO) MVP.

The goal is to demonstrate a complete, secure, observable, and usable try-on product journey on a real backend, physical mobile device, and configured VTO AI provider—moving from unit-tested components to an auditable release gate.

---

## 2. End-to-End Scope

The release candidate covers the 12 unified stages of the VTO user journey:
1. **Product Discovery**: Browse and retrieve garments from authorized e-commerce catalog sources.
2. **Garment Eligibility**: Verify image dimensions, category, provenance, and VTO commercial rights.
3. **User Preparation**: Select an eligible user photo and verify active, versioned user consent.
4. **Job Creation**: Authenticated, authorized, validated, and idempotent try-on job persistence.
5. **Asynchronous AI Processing**: Worker claims job, submits image pair to provider, and manages polling.
6. **Result Validation**: Structural safety, resolution, luminance, and artifact defect inspection.
7. **Secure Artifact Delivery**: Store privately in S3; issue authenticated, expiring signed URLs.
8. **Mobile Experience**: Live polling, before/after toggle, failure diagnostics, and safe retries.
9. **Wardrobe Persistence**: Save try-on look using true canonical garment ID and artifact UUID.
10. **Retailer Shopping Handoff**: Compare merchant offers; redirect via validated retailer allowlist.
11. **Feedback & Quality Learning**: Capture 5-star perceived realism, purchase confidence, and diagnostic issue tags.
12. **Privacy & Retention**: Enforce automated DPDP cascading erasure and retention cleanup.

---

## 3. Mandatory Release Gates

Release clearance requires all six gates defined in [`docs/release/gates.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/release/gates.md) to reach `passed` status with verifiable evidence cards:

| Gate | Title | Threshold Required for Launch | Evidence Document |
|:---|:---|:---|:---|
| **G1** | End-to-End User Journey on Real Stack | 100% core loop functional on physical device with real backend & real AI provider | `docs/evidence/g1-e2e.md` |
| **G2** | ML Quality & VLM Accuracy | VLM extraction accuracy $\ge 90\%$; Ranker nDCG@10 $\ge 0.75$ | `docs/evidence/g2-quality.md` |
| **G3** | Visual Quality, Latency & Load Tests | Realism mean $\ge 3.5/5.0$; P95 try-on latency $\le 45\text{s}$; 50 RPS system load test | `docs/evidence/g3-performance.md` |
| **G4** | Privacy, Legal Counsel & Recovery Drills | Outside counsel sign-off on 10 DPDP questions; restore drill RTO $\le 4\text{h}$ | `docs/evidence/g4-privacy-rto.md` |
| **G5** | Commercial Licences & Vendor DPA | 100% license-cleared catalog provenance; executed commercial DPA with try-on vendor | `docs/evidence/g5-commercial.md` |
| **G6** | Closed Pilot Evaluation | 20–40 participants; $\ge 75\%$ acceptable realism; 0 unresolved stop rules | `docs/evidence/g6-pilot.md` |

---

## 4. Required Failure & Resilience Tests

The release candidate must be subjected to real-world edge cases and failure modes:
1. **Invalid Garment Rights**: Garment marked `rights_tryon=False` is rejected at job creation.
2. **Missing / Revoked Consent**: User without active body photo consent cannot initiate try-on; consent revocation purges in-flight artifacts.
3. **Idempotent Job Retries**: Submitting same user idempotency key returns existing job; does not trigger duplicate inference.
4. **Provider Outage & Timeouts**: Worker recovers jobs upon timeout; preserves provider job ID; try-on kill switch protects API.
5. **Corrupted or Low-Quality Image Output**: Provider output failing luminance or resolution checks is rejected and not published.
6. **Artifact Authorization & Isolation**: User B cannot fetch or delete User A's private artifacts or wardrobe snapshots.
7. **Expired Signed URLs**: Expired presigned URLs return 403; mobile client queries job status to receive a refreshed, authorized URL.
8. **Out-of-Stock Offer Handoff**: Out-of-stock merchant offer cannot generate buy clicks or redirects.
9. **Worker Crash & Recovery**: Stale job recovery sweep re-claims abandoned jobs without duplicating inference.

---

## 5. Machine-Readable Evidence Manifest

Release gate enforcement is driven by `docs/release/vto-release-evidence.json` (and verified by `scripts/release/validate_vto_release.py`).

Each gate must provide:
- Commit SHA and target environment (`staging` or `prod`).
- Dated evidence document references (`docs/evidence/g*-*.md`).
- Metric numbers matching or exceeding the pre-registered thresholds.
- Founder / release owner sign-off.

---

## 6. Execution Commands

```bash
# 1. Run release-gate validator
uv run python scripts/release/validate_vto_release.py

# 2. Run release-gate validator test suite
uv run pytest tests/unit/test_vto_final_release_gate.py -v

# 3. Run post-deployment smoke test
uv run python scripts/release/smoke.py --base "$API_BASE" --token "$SMOKE_TOKEN"

# 4. Run local backend quality gate
bash scripts/ci/local_gate.sh

# 5. Run mobile quality gate
cd mobile && npm run typecheck && npm test -- --runInBand
```

---

## 7. Release Decision & Launch Criteria

- The release owner may approve MVP release only when all mandatory gates have passed and their evidence cards have been independently audited.
- A failed gate blocks release. A waiver must be formally documented and must never override legal, privacy, consent, or commercial-rights requirements.
- **Current Release Status**: **NOT CLEARED** — All six release gates remain unmeasured pending real-world provider inference, physical-device testing, counsel review, and closed-pilot execution. Green CI is necessary, but not sufficient for release.
