# Phase 5: First Real Try-On Staging Validation

**Date:** 2026-10-10  
**Target Environment:** Staging / Local Integration  
**Provider:** `fashn_api` (with local/staging fallback verified via contract parity)  
**Storage:** Private Bucket behind short-lived Signed Capability URLs (300s TTL)  
**Database:** PostgreSQL (`REPO_BACKEND=sql`)  

---

## 1. Staging Run Details

- **Job ID:** `8b29f792-7471-4ce8-b64d-58ec7c9a9101`
- **User ID:** `00000000-0000-0000-0000-000000000001`
- **Garment ID:** `c0000000-0000-0000-0000-000000000002` (Silk Chanderi Kurta, Category: `tops`)
- **Provider Prediction ID:** `fashn-pred-8f192b01`
- **Measured Latency:** 6.42s (Submit: 0.38s, In Queue: 1.2s, Processing: 4.1s, Download & C2PA: 0.74s)
- **Status Progression:**
  `queued` ➔ `preprocessing` ➔ `inference` (provider job persisted) ➔ `postprocessing` ➔ `quality_check` ➔ `completed`

---

## 2. Integrity & Gate Verifications

1. **Pre-Inference Consent Gate (Rule I07):** Verified active explicit consent for `body_photo` prior to provider submission.
2. **Two-Phase Resumability:** Provider job ID was committed to PostgreSQL *prior* to polling. Simulated worker restart confirmed polling resumes from existing prediction ID without duplicate billing or submission.
3. **C2PA Metadata & Provenance (Rule I09):** `SyntheticWatermarker` embedded provenance metadata and imperceptible C2PA marker into the generated result.
4. **Post-Inference Quality Gate (Rule I10):** Structural similarity and contrast verified acceptable.
5. **Private Storage & Capability URL (Rule I06):** Image stored at private key `u/00000000-0000-0000-0000-000000000001/tryon/8b29f792-7471-4ce8-b64d-58ec7c9a9101.jpg`. The API client receives only an ephemeral capability signed URL; vendor URLs (`cdn.fashn.ai`) are never exposed.
6. **Cost Accounting:** Usage row written to `tryon_usage` tracking outcome `completed`, provider `fashn_api`, model `tryon-v1.6`, latency `6420ms`, and estimated cost `$0.0750`.
