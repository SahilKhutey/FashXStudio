# Legal Counsel Review Briefing Pack

**Prepared For**: Outside Legal Counsel (Technology, Media & Telecommunications Practice)  
**Client Entity**: FashXStudio  
**Jurisdiction**: Republic of India  
**Date**: October 2026  
**Purpose**: Pre-Pilot Regulatory Review & Sign-Off (Release Gate G4)  

---

## 1. Executive Summary & Application Overview

FashXStudio is an AI-powered fashion discovery and virtual styling mobile application. Users upload self-portraits to preview catalog garments (from cleared brand feeds including Flipkart, Myntra, etc.) before clicking out to merchant websites to purchase.

All primary hosting, storage, and databases reside in **AWS Mumbai (`ap-south-1`)**.

---

## 2. Bundled Compliance Documentation

The following finalized legal and compliance artifacts are prepared for counsel's review:
1. **[Personal Data Inventory](./data-inventory.md)**: Exhaustive catalog of all personal data collected, storage location, encryption, and retention.
2. **[Processor Register & DPAs](./processors.md)**: Inventory of third-party processors (AWS, Supabase, FASHN AI, affiliate networks) and contractual terms.
3. **[Data Retention Schedule](./retention.md)**: Reconciling DPDP Rule 8(3) and CERT-In 180-day logging with user right to erasure.
4. **[Privacy Policy](./privacy-policy.md)** & **[Terms of Use](./terms.md)**: Consumer-facing policies with mandatory 18+ age restriction and AI simulation disclaimers.
5. **[Pilot Participant Agreement](./pilot-terms.md)**: Specific terms for 100 invited closed beta testers.
6. **[Account Deletion & Erasure Copy](./deletion-page.md)**: DPDP Section 12 1-click erasure interface.
7. **[Consent Screens & Multilingual Notice](./consent-text.md)**: English and Hindi onboarding notices complying with DPDP Section 6.
8. **[Breach Response Runbook](../runbooks/breach-response.md)**: Incident workflows for the 6-hour CERT-In clock and 72-hour DPB clock.

---

## 3. Statutory Compliance Mapping (DPDP Act, 2023)

| DPDP Section | Statutory Obligation | FashXStudio Implementation |
| :--- | :--- | :--- |
| **Section 6** | Notice & Consent Architecture | Granular, unconditional opt-in prior to photo capture. Hindi summary provided. Immutably recorded in `consent_records`. |
| **Section 7** | Legitimate Uses | Limited to internal analytics and CERT-In traffic security logging. |
| **Section 8** | Technical & Organizational Safeguards | AES-256-GCM encryption at rest, TLS 1.3 in transit, automated PII scrubbing filter (`RedactFilter`) across all logs. |
| **Section 8(6)** | Personal Data Breach Reporting | Automated alerting, 6-hour CERT-In notification protocol, 72-hour DPB protocol. |
| **Section 9** | Children's Data Processing | Strict 18+ barrier (Rule I17). Zero processing of minor data; no tracking or behavioral profiling of children. |
| **Section 11** | Right to Access Information | Self-service data export endpoint (`GET /api/v1/me/export`) delivering complete data package within 72 hours. |
| **Section 12** | Right to Correction and Erasure | Instant cascading delete via `erase_account()`, immediate S3 bucket prefix purge, minimal pseudonymous tombstone replay. |
| **Section 13** | Grievance Redressal Mechanism | Published Data Protection Officer contact (`dpo@fashx.studio`) with 72-hour guaranteed resolution SLA. |

---

## 4. Specific Questions for Counsel Opinion

1. **Photo Upload Consent Scope**:  
   *Question*: Does DPDP Section 6 require a separate modal consent prompt before *each* subsequent photo upload, or is an account-level consent renewed upon major terms revisions sufficient, provided users have persistent 1-click deletion access in Settings?
2. **Consumer Protection (E-Commerce) Rules 2020**:  
   *Question*: Given that FashXStudio acts solely as an affiliate discovery link-out engine (we do not process consumer payments, maintain inventory, or act as the contracting merchant of record), does FashXStudio fall outside the definition of an "e-commerce entity" under the Consumer Protection (E-Commerce) Rules?
3. **Significant Data Fiduciary (SDF) Classification**:  
   *Question*: Based on our pilot volume (100 invited users, 5k-10k catalog items), can counsel confirm that FashXStudio does not meet the criteria for designation as a Significant Data Fiduciary under Section 10?
4. **Separate Photo & Try-On Vendor Consent**:  
   *Question*: Under DPDP Act 2023 Section 6 and Section 9, is separate, explicit consent required for processing the user's body photo versus transferring/processing it with an external cloud try-on model vendor (Data Processor), or does a granular unbundled affirmation covering both during onboarding satisfy statutory requirements?
5. **Post-Erasure Retention of Minimal Consent Audit Trail**:  
   *Question*: Under DPDP Act 2023 Section 12 (Right to Erasure) read with Section 8(7) (Data Retention Limitation), when a data principal exercises their right to complete account erasure, is FashXStudio permitted (or legally required for evidentiary defense under Section 7/statute of limitations) to retain an immutable, pseudonymous or hashed log of the historical consent granted and the timestamp of erasure, or must all records in `consent_records` be completely hard-deleted alongside the personal data?
