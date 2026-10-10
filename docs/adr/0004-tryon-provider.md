# ADR-0004: Try-on Provider Selection

- **Status:** Accepted
- **Date:** 2026-10-10
- **Owner:** Sahil Khutey

---

## 1. Context

Release Gate G5 (commercial clearance) and Gates G2/G3 (ML quality and latency) require a license-cleared virtual try-on system that executes end-to-end via the API on real user photos and catalog garments. Previous iterations relied on `MockTryOnAdapter` or research models carrying non-commercial licenses (StableVITON, OOTDiffusion, IDM-VTON, CatVTON), which are strictly forbidden in production by Rule I08.

With FASHN's open-source release of VTON v1.5 (Apache-2.0) and the availability of commercial hosted APIs (FASHN hosted API v1.6 / Try-On Max, Google Vertex AI `virtual-try-on-001`), legitimate commercial production paths now exist.

---

## 2. Options Considered

### Option A: FASHN Hosted API (tryon-v1.6 / Try-On Max) — Pilot Default
- **Role:** Pilot default provider.
- **Pros:** No GPU cluster operations or auto-scaling overhead. Managed infrastructure returning 864x1296 images in 5-8s. Commercial output license, signed DPA, and automated 72-hour input deletion.
- **Cons:** External vendor egress, per-generation credit cost (~$0.075 / image).

### Option B: Google Vertex AI (`virtual-try-on-001`) — Challenger
- **Role:** Challenger candidate.
- **Pros:** Enterprise cloud backing, consolidated billing on GCP, strong data governance agreements.
- **Cons:** Quota limitations (50 req/min), lifecycle deprecation risks.

### Option C: Self-Hosted FASHN VTON v1.5 (Apache-2.0) — Spike Only
- **Role:** Fallback / zero-vendor path.
- **Pros:** Full data residency (zero external network egress), fixed compute cost on reserved GPUs.
- **Cons:** High operational overhead (GPU instance management, cold-start latency, model updates, human-parser license dependency).

---

## 3. Pre-Registered Acceptance Thresholds (Committed Before Evaluation)

To prevent bias after inspecting results, the evaluation scorecard was evaluated against pre-registered criteria:

| Metric | Threshold |
|---|---|
| Completion rate (no unhandled error) | ≥ 95% |
| Overall acceptability rated ≥ 4/5 | ≥ 70% of results |
| Overall acceptability rated ≤ 2/5 ("unacceptable") | ≤ 10% of results |
| Identity & skin tone preserved (rated ≥ 4) | ≥ 95% of results |
| p95 submit-to-image latency (hosted) | ≤ 30 s |
| Cost per accepted result (including retries) | ≤ $0.15 |
| Fairness across slices (skin tone, body type, ethnic wear) | No slice mean score > 0.5 below global mean |

---

## 4. Vendor DPA Checklist & Data Governance Answers

| Question | FASHN Hosted API | Google Vertex AI | Self-Hosted v1.5 |
|---|---|---|---|
| User input used for training? | **No** (Contractually excluded in DPA) | **No** (Standard GCP commitment) | **No** (Zero external egress) |
| Retention period | 72 hours auto-delete on CDN/servers | In-memory processing / ephemeral | 0 hours (Ephemeral GPU memory) |
| Can deletion be triggered? | Yes (API or support ticket) | Not retained beyond request | N/A (Local control) |
| Processing regions & sub-processors | AWS / Cloudflare EU & US | GCP regions (us-central1, europe-west4) | Dedicated self-hosted VPC |
| Commercial output ownership | Customer owns generated outputs | Customer owns generated outputs | Full ownership under Apache-2.0 |
| Content moderation | Strict nudity & minor safety filter | Vertex AI safety filters | Custom pre-inference quality gate |
| Breach notification SLA | ≤ 48 hours | ≤ 48 hours | N/A (Internal incident response) |

---

## 5. Evaluation Results

Full details recorded in [`docs/logs/phase5-eval-2026-10-10.md`](../logs/phase5-eval-2026-10-10.md):

- **Completion Rate:** 97.5% (PASS vs ≥ 95%)
- **Overall Acceptability (≥4/5):** 76.2% (PASS vs ≥ 70%)
- **Unacceptable Rate (≤2/5):** 6.2% (PASS vs ≤ 10%)
- **Identity & Skin Tone Preserved:** 96.2% (PASS vs ≥ 95%)
- **p95 Latency:** 11.4 s (PASS vs ≤ 30 s)
- **Cost per Accepted Result:** $0.0984 (PASS vs ≤ $0.15)
- **Fairness Delta:** Max slice delta -0.28 on draped ethnic wear (PASS vs max -0.50)

---

## 6. Decision and Consequences

**Decision:** Adopt **Option A (FASHN Hosted API `tryon-v1.6` / Try-On Max)** as the primary try-on provider for the FashX Studio pilot launch.

### Consequences:
1. **Commercial Clearance (Gate G5):** Approved with commercial output license and signed DPA. Non-commercial models remain strictly forbidden (Rule I08).
2. **Capability Gating (Step 5.20):** Complex unanchored drape formats (e.g. Sarees and Lehengas with floating dupattas) are gated via catalog attribute `tryon_supported = false`. Supported apparel (`tops`, `bottoms`, structured kurtas) represent the pilot launch scope.
3. **Safety & Budget Controls:** Redis circuit breaker (`Breaker`), daily budget ceiling (`TRYON_DAILY_BUDGET_USD`), and user daily quota (`TRYON_USER_DAILY_CAP`) protect against vendor runaway costs.
4. **Data Privacy (Gate G4):** Ephemeral preprocessed payloads, zero vendor URLs returned to users, C2PA watermark embedding, and cascading erasure on consent revocation.
