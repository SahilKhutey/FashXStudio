# DPDP Compliance Calendar & Statutory Countdown (Target: 14 May 2027)

- **Legislation:** Digital Personal Data Protection Act, 2023 (DPDP Act) & DPDP Rules, 2025
- **Notification Date:** 13 November 2025
- **Enforcement Date:** ~13–14 May 2027 (18-Month Statutory Window)
- **FashXStudio Role (Path B):** Data Processor (Merchant Brands are Data Fiduciaries)

---

## 1. Compliance Architecture Summary

Under Path B B2B architecture:
- **Shopper Data:** Processed strictly on behalf of the merchant brand. Body photos are held in **Ephemeral Processing Mode** (max 24h retention, encrypted at rest, zero retention for model training).
- **Merchant Account Data:** Retained for the duration of the commercial agreement + statutory accounting periods.
- **Audit Logs:** Personal data access, admin actions, and API traffic logs retained for exactly 1 year per Rule 8(3) requirements.

---

## 2. Milestone Countdown to 14 May 2027

| Milestone Target | Window | Key Deliverables & Compliance Gate | Status |
|---|---|---|---|
| **Phase 12 Foundation** | Oct – Dec 2026 | - Formalize standard Data Processing Agreement (DPA) for all B2B brand partners.<br>- Verify 24h automated purge cron in storage infrastructure.<br>- Implement minimum 1-year activity logging policy (`Rule 8(3)`). | **Active** |
| **Q1 2027 Audit** | Jan – Mar 2027 | - Run Data Protection Board (DPB) breach notification drill (two-stage: immediate notice + 72h detailed report).<br>- Test complete data portability & account erasure endpoints (`erase_account`, `erase_biometrics`).<br>- Review all 3rd-party subprocessors (AWS, Supabase, Cloudflare). | Scheduled |
| **Q2 2027 Final Hardening** | Apr – May 2027 | - Formalize designated Grievance Redressal Officer & publish contact on corporate site.<br>- External third-party legal and security compliance audit sign-off.<br>- Verify multi-lingual privacy notice support (English + Schedule 8 Indian languages). | Scheduled |
| **Statutory Go-Live** | **14 May 2027** | - **DPDP Act Full Operational Force**.<br>- 100% compliant processor operations across all live brand storefronts. | Target |

---

## 3. Statutory Requirements Checklist

### A. Notice & Consent (Rules 3, 4)
- [x] Clear, standalone notice presented before shopper photo capture in widget.
- [x] Itemized purpose explanation ("Virtual fit simulation only; auto-deleted in 24 hours").
- [x] Multilingual capability ready for merchant storefront localized notices.

### B. Security Safeguards & Processing Contracts (Rule 8)
- [x] AES-256 encryption at rest for all temporary storage artifacts.
- [x] TLS 1.3 enforced for all API and widget communication.
- [x] Strict tenant isolation enforced at query level via `tenant_id` scopes.
- [x] Standard DPA signed with every partner merchant before widget goes live on production PDPs.

### C. Incident & Breach Management (Rule 9)
- [x] Two-stage reporting runbook documented in `docs/runbooks/breach-incident.md`.
- [x] Stage 1: Immediate notification to the Data Protection Board upon confirmation of personal data breach.
- [x] Stage 2: Comprehensive technical forensic report filed within 72 hours.
- [x] Notification to affected merchants within 12 hours of confirmed breach.

### D. Activity Log Retention (Rule 8(3))
- [x] Immutable audit trail of session access and administrative actions stored for minimum 1 year in tamper-resistant cold storage.
- [x] Standing SQL view `scripts/operations/views.sql` ensures internal visibility without exposing raw biometrics.
