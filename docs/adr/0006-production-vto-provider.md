# ADR-0006: Production Virtual Try-On Provider

- **Status:** PROPOSED
- **Date:** 2026-11-23
- **Decision owners:** FashXStudio engineering and product owners

---

## 1. Context

FashXStudio requires a production virtual try-on (VTO) inference capability using a shopper-provided reference photograph and an authorized merchant product image.

The repository contains an existing provider abstraction (`TryOnAdapter` and `TryOnModelAdapterPort`) and a concrete `FashnApiAdapter` implementing integration with the FASHN Hosted API. However, the presence of this adapter in the codebase does not establish live commercial integration, endpoint compatibility across model variants, or production readiness.

Furthermore, processing user biometric imagery (reference photos) and merchant catalog images involves strict data protection, intellectual property, and privacy requirements under Indian DPDP regulations and FashXStudio architecture invariants (Rule I06 and Rule I08).

---

## 2. Decision

1. **Evaluate FASHN as the Initial Hosted VTO Provider**:
   - Retain the existing provider-neutral adapter interface (`fashx.application.ports.tryon.TryOnAdapter` and `fashx.tryon.ports.TryOnModelAdapterPort`).
   - Validate and benchmark the existing FASHN integration first before considering provider replacements or self-hosted model projects.
   - Do not begin a self-hosted research model implementation during this phase due to GPU infrastructure overhead, cold-start latency, and non-commercial license prohibitions (Rule I08).

2. **Benchmarking Strategy**:
   - Evaluate two candidate endpoints on a controlled Indian fashion dataset:
     - **FASHN Try-On Max**: Premium fidelity, broader item support (including accessories/shoes), prompt customization.
     - **FASHN Virtual Try-On v1.6**: Lightweight, fast (5–8s latency), 1 credit per output ($0.075 on-demand).
   - Selection will be determined by benchmark quality, latency, failure rate, and cost-per-usable-output, rather than vendor marketing materials.

---

## 3. Candidate Endpoints

| Endpoint | Primary Use Case | Output Resolution | Est. Latency | Nom. Cost | Target Apparel Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Try-On Max** | Premium evaluation | Up to 4K | 15–30s | Variable (by res/mode) | Tops, bottoms, kurtas, one-pieces, accessories |
| **Virtual Try-On v1.6** | Real-time e-commerce baseline | 864 × 1296 px | 5–17s | 1 credit ($0.075) | Tops, bottoms, one-pieces, auto |

Final endpoint and model selection will be configurable via application settings (`FASHN_MODEL`, `FASHN_MODE`) rather than hardcoded.

---

## 4. Initial Supported Categories

For the initial pilot and controlled rollout:
- **T-shirts & Shirts** (Upper-body / `tops`)
- **Trousers & Skirts** (Lower-body / `bottoms`)
- **Selected Structured Kurtas** (Upper-body / `tops`)
- **Dresses & Jumpsuits** (One-piece / `one-pieces`) — subject to separate evaluation.

**Explicitly Unsupported in Pilot**:
- Unanchored drape formats (e.g., Sarees, Lehengas with floating dupattas).
- Garments tagged with `tryon_supported = false` in the catalog.
- Products where the merchant source lacks `rights_tryon = true`.

---

## 5. Privacy and Security Requirements

1. **Explicit Shopper Consent**:
   - Valid, unrevoked consent (`body_photo`) must exist prior to queuing, before inference dispatch, after inference completion, and prior to artifact persistence.
   - Consent revocation immediately cascades: mid-flight jobs cancel and temporary private storage objects are deleted.

2. **Merchant Rights Clearance**:
   - Only products from sources with `status == "cleared"` and active `rights_tryon == True` may be processed.

3. **Secure In-Flight Transmission**:
   - Shopper reference photos must be transmitted via private, short-lived signed URLs or ephemeral base64 payloads.
   - No long-lived public URLs for shopper photos may ever be provided to third-party providers.

4. **Credential Isolation**:
   - Provider API keys must never be bundled into the mobile app, committed to source repositories, or exposed in client-facing responses.
   - Keys are injected via AWS Secrets Manager (`/fashx/{env}/tryon/fashn-api-key`) and resolved into memory as `SecretStr`.

5. **Data Residency & Subprocessors**:
   - Vendor DPA and complete subprocessor list must be reviewed and signed.
   - Vendor must provide written confirmation that customer images and inputs are **not** used for model training or retained beyond ephemeral request processing.

6. **Watermarking & Provenance (Rule I09)**:
   - All rendered outputs must have synthetic media provenance metadata (C2PA-compatible tags) and a visible preview watermark applied prior to delivery.

---

## 6. Operational Requirements

1. **Asynchronous Decoupled Execution**:
   - Inference runs asynchronously via Celery worker queue (`fashx.workers.app.process_tryon_job`), never blocking HTTP API requests.
2. **Durable Job State & Idempotency**:
   - Job creation is protected by client idempotency keys (`Idempotency-Key`).
   - Provider prediction IDs are persisted to enable crash recovery without duplicate API submissions or double-billing.
3. **Resilience & Rate Limiting**:
   - Circuit breaker (`Breaker` / `InMemoryBreaker`) trips on consecutive vendor failures (5 failures in 60s window).
   - Polling utilizes exponential backoff with jitter to stay well below vendor status polling limits (50 req/10s).
   - Bounded retries: maximum 3 attempts with exponential delay for transient provider errors.
4. **Cost & Quota Safeguards**:
   - Daily user try-on cap (`TRYON_USER_DAILY_CAP`, default 20 jobs/day).
   - Daily tenant budget ceiling (`TRYON_DAILY_BUDGET_USD`, default $20.00/day).
   - Provider usage and estimated costs recorded in `TryOnUsage`.

---

## 7. Alternatives Considered

1. **Existing Mock Provider (`MockTryOnAdapter`)**:
   - Useful for unit tests, contracts, and CI environments.
   - Strictly forbidden in production (Rule I08) and blocked by license guards (`assert_production_license`).
2. **Self-Hosted Research Models (StableVITON, OOTDiffusion, IDM-VTON, CatVTON)**:
   - Carry non-commercial research licenses (CC-BY-NC) strictly prohibited in commercial production.
   - Require dedicated GPU clusters (A10G/A100), increasing operational complexity and fixed infrastructure cost.
3. **Google Vertex AI (`virtual-try-on-001`)**:
   - Maintained as an alternative challenger for enterprise multi-cloud evaluation.
4. **Additional Commercial Providers**:
   - The provider abstraction allows integrating secondary commercial vendors via new adapters without modifying domain workflows.

---

## 8. Approval Conditions (Exit Gate)

Before promoting FASHN to `PRODUCTION_VERIFIED`:
- [ ] Valid live API credentials provisioned in AWS Secrets Manager for dev/staging.
- [ ] Live API integration tests (`VTO-PROV-001` through `VTO-PROV-018`) successfully executed on non-production test images.
- [ ] Image outputs validated by `PostInferenceQualityValidator` and correctly watermarked.
- [ ] Quality benchmark completed on the controlled Indian fashion dataset across candidate endpoints (Try-On Max vs v1.6).
- [ ] Commercial agreement, Data Processing Addendum (DPA), and subprocessor list approved by legal counsel.
- [ ] Confirmation of zero model training on customer data and documented retention behavior.
- [ ] Cost-per-usable-result calculated and within approved budget boundaries.

---

## 9. Consequences

- **Vendor Dependency**: FashXStudio depends initially on an external managed inference API.
- **Portability**: The provider-neutral adapter architecture isolates domain, worker, and database models from vendor-specific changes.
- **Egress & Latency**: Real-world try-on latency will depend on network egress and vendor inference speed, requiring clear client-side progress indicators and notifications.
