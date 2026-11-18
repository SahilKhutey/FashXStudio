# Merchant Onboarding Checklist

**Phase 05 — Workstream 5.1 (Merchant and Source Authorization)**  
**Standard**: SOC2 / ISO 27001 / FashXStudio Catalog Policy Framework  
**Enforcement**: Strict Fail-Closed Verification Baseline

---

## 1. Overview
FashXStudio acquires catalog data only from verified merchants and authorized sources. The public availability of product listings online does not convey any right to extract, store, process with AI, or monetize such data. Every merchant onboarding onto FashXStudio must successfully clear this checklist before any integration source or product ingestion can be scheduled.

---

## 2. Onboarding Phases

```
+-------------------+      +--------------------+      +--------------------+      +--------------------+
| 1. Registration   | ---> | 2. Legal Review    | ---> | 3. Technical Match | ---> | 4. Source Cleared  |
| Identity & Form   |      | MCA, GSTIN, Docs   |      | Endpoint & Security|      | Active in Registry |
+-------------------+      +--------------------+      +--------------------+      +--------------------+
```

### Stage 1: Identity & Legal Registration
- [ ] **Legal Business Name Verification**: Legal name exactly matches official business registration (e.g., MCA / RoC in India, Companies House in UK, Delaware Secretary of State in US).
- [ ] **Corporate Registration Reference**: Valid Corporate Identification Number (CIN), GSTIN (Goods & Services Tax Identification Number), or national tax ID recorded and verified against government registers.
- [ ] **Registered Office Address**: Official legal operating address on record.
- [ ] **Designated Responsible Officers**:
  - Primary Business / Merchant Contact (Name, corporate email, phone).
  - Technical / API Integration Lead (Name, corporate email, phone).
  - Designated Takedown / Copyright Officer (Monitored mailbox, 24/7 turnaround SLA).

### Stage 2: Contractual & Permission Authorization
- [ ] **Master Services Agreement (MSA) / Data License**: Signed agreement between merchant entity and FashXStudio.
- [ ] **Document Storage & Cryptographic Verification**:
  - Executed PDF archived in secure, versioned object store.
  - SHA-256 cryptographic hash calculated, verified, and stored in `catalog_authorization_evidence`.
  - Agreement version and countersignature metadata recorded.
- [ ] **Permission Scope Explicitly Defined**:
  - `PRODUCT_DATA_READ`: Authorized.
  - `PRODUCT_DATA_STORE`: Authorized.
  - `PRODUCT_DISPLAY`: Explicit display rights confirmed.
  - `IMAGE_FETCH` & `IMAGE_DISPLAY`: Explicit image rights confirmed.
  - `IMAGE_AI_PROCESS` & `VTO_PROCESS`: AI analysis and try-on specifically negotiated and granted (NEVER inferred from display permissions).
  - `DERIVATIVE_CREATE`: Generation of standardized garment cutouts and masks approved.
  - `MERCHANT_REDIRECT`: Redirect URLs and affiliate terms aligned.

### Stage 3: Technical Security & Integration Pre-Flight
- [ ] **Access Method Established**: OAuth2 client credentials, signed HMAC, or HTTPS feed with mutual TLS/API keys.
- [ ] **Credentials Stored Securely**: API secrets stored in AWS Secrets Manager; only secret ARN/references (`credential_secret_ref`) stored in database.
- [ ] **Rate Limits & Sync Cadence Agreed**: Max requests per second (RPS) configured; polling interval set (`refresh_hours`).
- [ ] **Category & Market Restrictions Configured**: Allowlist of target merchandise categories (e.g., `apparel`, `footwear`) and geographic markets (e.g., `IN`).

### Stage 4: Admin Verification & Activation
- [ ] **Reviewer Attestation**: FashXStudio catalog administrator reviews evidence and executes `POST /api/v1/admin/catalog/merchants/{id}/verify` with status `VERIFIED`.
- [ ] **Source Activation Pre-Conditions Met**:
  - Merchant status == `VERIFIED`.
  - Evidence status == `VERIFIED`.
  - Granular permissions mapped in `catalog_source_permissions`.
  - Source status transitioned to `ACTIVE`.

---

## 3. SLA and Audit Requirements
- Verification turnaround SLA: 2 business days from document receipt.
- Annual recertification: Required every 12 months; automated warnings at 30, 14, and 7 days prior to expiry.
- Record retention: Contractual evidence and audit decisions retained for 7 years post-termination.
