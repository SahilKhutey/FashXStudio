# FashXStudio — Assumptions & Risk Governance Register

**Document ID:** `FASHX-RSK-001`  
**Version:** `1.0 — Approved Baseline`  
**Date:** `10 November 2026`  
**Status:** `Approved Risk Baseline`  
**Scope:** `Phase 01 — Product Assumptions & Technical Risk Mitigation`  

---

## 1. Assumptions Register (A-01 – A-12)

In accordance with [AGENTS.md](file:///c:/Users/ASUS/Documents/FashXStudio/AGENTS.md), all core product assumptions remain classified as **`Unvalidated`** until supported by documented merchant agreements, customer interview transcripts, or live pilot telemetry.

| ID | Assumption Statement | Business Significance | Empirical Validation Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **A-01** | Shoppers want to see garments rendered on their own photos before buying. | Core product value proposition | 15 shopper prototype discovery interviews | **Unvalidated** |
| **A-02** | Personal-image VTO increases purchase confidence and reduces hesitation. | Primary product differentiator | Before/after user confidence testing | **Unvalidated** |
| **A-03** | Shoppers are willing to upload full-body photos when privacy is explicit. | User acquisition & activation | Onboarding photo upload completion rate | **Unvalidated** |
| **A-04** | D2C brands will authorize product feeds and copyrighted imagery for AI VTO. | Catalog acquisition model | Signed pilot agreements & DPA execution | **Unvalidated** |
| **A-05** | Hosted diffusion models (FASHN) deliver acceptable photorealism on kurtas. | Core technical feasibility | 50-sample human quality benchmark review | **Unverified** |
| **A-06** | Upper-body categories (T-shirts, shirts, kurtas) are optimal for the MVP. | Scope control & latency management | Category-specific error and return audits | **Unvalidated** |
| **A-07** | Brand founders value engagement telemetry and try-on interaction metrics. | B2B commercial value proposition | Merchant discovery interviews & reviews | **Unvalidated** |
| **A-08** | A B2B-first approach provides sustainable shopper acquisition without high CAC.| Go-to-market efficiency | Design partner traffic analysis | **Unvalidated** |
| **A-09** | GPU inference and storage costs allow sustainable $\ge 65\%$ gross margins. | Long-term business viability | Production unit economics accounting | **Unvalidated** |
| **A-10** | Shoppers value saving styled looks to an in-app digital wardrobe. | Retention and repeat usage | Look save rate telemetry ($\ge 20\%$ target) | **Unvalidated** |
| **A-11** | Outbound merchant redirection generates qualified purchase intent. | Commerce partner value | Outbound click tracking via `/outbound-clicks`| **Unvalidated** |
| **A-12** | A lightweight 30-second style quiz is sufficient for initial discovery. | Onboarding simplicity | Profile completion telemetry ($\ge 65\%$ target) | **Unvalidated** |

---

## 2. Comprehensive Risk Register (R-01 – R-16)

| Risk ID | Risk Description | Likelihood | Impact | Core Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | VTO outputs exhibit unnatural warping or artifacts. | High | Critical | Dual-reviewer human evaluation panel; strict category boundaries; automated artifact filters. |
| **R-02** | Garment details (logos, prints, buttons) are altered by AI. | High | High | Garment preservation rubric (8-point checklist); source image pre-segmentation. |
| **R-03** | Shoppers interpret visual simulation as a fit guarantee. | Medium | Critical | Prominent visual simulation disclaimer on PDP and result screens; size chart modal. |
| **R-04** | Merchant lacks authority to license studio images for AI. | Medium | Critical | Modular legal pack requiring explicit warranty of copyright ownership before publication. |
| **R-05** | Biometric data leak or user photo privacy violation. | Medium | Critical | Private S3 storage; time-limited presigned URLs; automated 24-hour buffer / 30-day purge; audit tombstones. |
| **R-06** | GPU inference costs exceed commercial pricing ceiling. | Medium | High | Automated ₹5,000 daily spend ceiling; per-user quota (5/day); single automated retry cap. |
| **R-07** | Hosted GPU provider experiences outages or high latency. | Medium | High | Circuit-breaker queue architecture; 30s timeout guard; graceful recoverable failure states. |
| **R-08** | Merchant catalog contains poor-resolution or missing images. | High | High | Automated ingestion quality gate enforcing $800 \times 1000$ px resolution and neutral backgrounds. |
| **R-09** | Ingested product pricing or stock becomes stale. | Medium | Medium | Daily incremental synchronization jobs; freshness timestamp displayed on PDP. |
| **R-10** | Shoppers abandon onboarding at photo upload screen. | Medium | High | Progressive onboarding (browse first, try on later); visual framing guidance modal. |
| **R-11** | Merchant onboarding stalls due to custom IT demands. | Medium | High | Assisted white-glove onboarding for design partner; standard CSV template support. |
| **R-12** | Analytics events are lost or duplicated during retries. | Medium | High | Universal event envelope with client idempotency keys and post-commit transactional outbox. |
| **R-13** | Pilot sample size is insufficient for statistical confidence. | High | Medium | Explicitly label metrics as qualitative directional hypotheses; report exact observation counts. |
| **R-14** | Brand disputes return rate or claims false fit liability. | Medium | Critical | Written agreement disclaiming physical sizing liability; terms mandate customer consults size chart. |
| **R-15** | Scope expands into frozen commerce features. | High | High | Strict enforcement of ADR-0001; router unmounting; mandatory change request protocol. |
| **R-16** | Outbound merchant destination URLs become 404 or broken. | Medium | Medium | Automated weekly URL health check crawler; fallback redirect to merchant root domain. |

---

## 3. Critical Risk Response Plans

### R-01: VTO Visual Quality Failure
- Restrict initial pilot strictly to Men's T-shirts, shirts, and structured straight-cut kurtas.
- If realism scores fall below 3.8/5, disable the affected category immediately and adjust prompt conditioning and segmentation masks.

### R-04: Image Licensing & Copyright Clearance
- Maintain decoupled database permission records (`MERCH_IMAGE_VTO`).
- Require merchant to sign explicit `PRODUCT_IMAGE_USAGE_PERMISSION.md` warranting indemnification against model agency copyright claims.

### R-05: Shopper Privacy & Biometric Security
- User photos are stored in non-public S3 buckets with server-side encryption (SSE-S3).
- User photos are never exposed via public URLs; all access uses presigned URLs expiring within 1 hour.
- Automated Celery worker sweeps database daily to tombstone expired assets and delete underlying S3 objects.

### R-03 / R-14: Fit Representation & Liability
- **Mandatory Product Notice:** *"Virtual Try-On is an AI-generated visual preview of garment appearance and drape. It does not measure physical fit or guarantee sizing. Please consult the brand's official size chart before purchasing."*
