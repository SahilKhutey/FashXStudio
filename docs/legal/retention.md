# Data Retention & Erasure Schedule

**Organization**: FashXStudio  
**Jurisdiction**: Republic of India (Digital Personal Data Protection Act, 2023 / DPDP Rules 2025; CERT-In Directions 2022)  
**Effective Date**: October 2026  
**Status**: Release Gate G4 Verified  

---

## 1. Statutory Framework

This schedule reconciles statutory record-keeping mandates in India with the data fiduciary obligations of purpose limitation, storage limitation, and the data principal's right to erasure (DPDP Section 12):

1. **DPDP Act 2023 & Rules 2025 (Rule 8(3))**: Personal data must not be retained beyond the period necessary for the specified purpose, except where retention is required under statutory law. Personal data, traffic data, and access logs must be maintained for at least 1 year in India (`ap-south-1`).
2. **CERT-In Directions (April 2022)**: ICT system logs and transaction logs must be securely maintained within Indian jurisdiction for at least 180 days.
3. **Right to Erasure (DPDP Section 12)**: Upon receipt of an erasure request or withdrawal of consent, personal data must be permanently erased within 48 hours, unless retained under statutory mandate.

---

## 2. Retention Matrix

| Data Category | Table / Storage Location | Retention Period | Trigger / Action at Expiry | Statutory Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Biometric & Self-Portraits** | `user_photos`, `media_objects`, S3 bucket (`u/{user_id}/`) | Active session / user life | Immediate hard deletion upon consent revocation or account erasure. Encrypted at rest (`AES-256-GCM`). | Purpose limitation: only used to render try-on output. |
| **Unsaved Try-On Artifacts** | `tryon_jobs`, `tryon_artifacts`, S3 bucket (`tryon/`) | **30 days** | Automated Celery job at 03:00 IST deletes S3 assets and database rows in batches of 500. | Storage limitation: temporary styling preview. |
| **Saved Closet Outfits** | `wardrobe_items`, `tryon_artifacts` | Lifetime of user account | Retained until explicitly removed by user or upon account closure. | User-directed persistent storage. |
| **Feed Impressions & Signals** | `feed_impressions`, `feed_signals` | **90 days** | Hard deletion of impression rows older than 90 days. Aggregated model weights persist. | Diminishing recommendation utility. |
| **Domain & Analytics Events** | `domain_events`, `analytics_events` | **12 months (365 days)** | Set `user_id = NULL` (irreversible pseudonymization / anonymization). | CERT-In 180-day & DPDP 1-year log retention while breaking link to user identity. |
| **Operational & Security Logs** | AWS CloudWatch Log Groups (`/ecs/fashx-api`) | **365 days (1 year)** | CloudWatch automated lifecycle expiration. All logs pre-filtered via `RedactFilter` (zero PII, zero tokens). | CERT-In 180-day ICT logging mandate in AWS Mumbai (`ap-south-1`). |
| **Erasure Tombstones** | `erasure_tombstones` | Indefinite (minimal) | Minimal cryptographic tombstone (`user_id`, `erased_at`) preserved to prevent resurrection upon backup restore. | Data integrity and permanent erasure enforcement. |

---

## 3. Automated Enforcement Mechanism

The cleanup pipeline is codified in `backend/fashx/application/retention.py` and scheduled via Celery Beat:

- **Schedule**: Nightly at 03:00 IST (21:30 UTC).
- **Execution**: S3 objects purged prior to database commits; database rows pruned using chunked transactions (`LIMIT 500`) to eliminate table locking.
- **Verification**: Nightly log emits structured count of deleted rows and purged S3 keys.
