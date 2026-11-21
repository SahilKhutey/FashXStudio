# FashXStudio — Consent Management Architecture & Policy

## 1. Governance Boundary & Core Invariant
At FashXStudio, **consent is decoupled from authentication and basic product discovery**.
- An authenticated shopper can discover garments, browse recommendations, and view catalog items without consenting to biometric or photo processing.
- Uploading a personal body photo or initiating virtual try-on requires **explicit, separate, and versioned consent**.
- Consents are recorded as immutable event streams in PostgreSQL (`consent_records` current state + `consent_events` append-only audit trail).
- Under DPDP Act 2023 and GDPR, consent withdrawal is immediately honored across both synchronous API access and active background processing pipelines.

---

## 2. Consent Taxonomy

| Consent Identifier | Scope & Purpose | Required Age Check | Storage & Retention |
| :--- | :--- | :--- | :--- |
| `terms_and_privacy` | Acceptance of platform Terms of Service & Privacy Policy | $\ge 18$ years | Retained while account is active |
| `body_photo` | Explicit permission to upload and store personal body photo | $\ge 18$ years | Erased on revocation or account deletion |
| `vto_processing` | Permission to perform virtual try-on inference on photo | $\ge 18$ years | Erased on revocation or account deletion |
| `third_party_vto` | Permission for external vendor ML processing (if applicable) | $\ge 18$ years | Erased on revocation or account deletion |
| `marketing_comms` | Optional promotional communication and styling updates | Not restricted | Updated on user preference change |

---

## 3. Database Schema & Constraints

### 3.1 `consent_records` Table
Current materialized consent state per user per data type:
- `user_id`: UUID (Foreign Key to `users.id` with `ON DELETE CASCADE`)
- `data_type`: VARCHAR(64) — e.g., `body_photo`, `terms_and_privacy`
- `granted`: BOOLEAN NOT NULL
- `consent_version`: VARCHAR(16) NOT NULL (e.g., `2026.1`)
- `is_18_or_older`: BOOLEAN NULL
- `consented_at`: TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `updated_at`: TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Integrity Constraints:**
- Primary Key: `(user_id, data_type)`
- Check Constraint: `ck_consent_granted_requires_adult`: `granted IS NOT TRUE OR is_18_or_older IS TRUE`
- Composite Index: `ix_consent_records_user_policy`: `(user_id, consent_version)`

### 3.2 `consent_events` Append-Only Audit Stream
Immutable event log of every consent grant, modification, and revocation:
- `id`: UUID Primary Key
- `user_id`: UUID (Foreign Key to `users.id` with `ON DELETE CASCADE`)
- `data_type`: VARCHAR(64) NOT NULL
- `granted`: BOOLEAN NOT NULL
- `consent_version`: VARCHAR(16) NOT NULL
- `policy_url`: VARCHAR(255) NULL
- `decision_source`: VARCHAR(64) NOT NULL (e.g., `api`, `profile_api`, `mobile_onboarding`)
- `created_at`: TIMESTAMPTZ NOT NULL DEFAULT NOW()

---

## 4. Server-Side Enforcement Rules

1. **Server-Side Verification**: Client-supplied boolean parameters (such as `has_consent=true` in request payloads) are strictly untrusted. All service operations must check `UserConsentRepository.has_consent(user_id, "body_photo")` against PostgreSQL.
2. **Double-Check on Asynchronous Pipelines**:
   - At job submission (`CreateTryOnJobUseCase`): Validates active consent before queuing.
   - At worker execution (`ProcessJobUseCase`): Re-queries database immediately before downloading media or invoking ML inference. If consent was revoked while the job was queued, worker cancels with failure reason `consent_revoked`.
3. **Cascading Biometric Deletion on Revocation**:
   - When `body_photo` consent is revoked via `PUT /api/v1/profile/consents/body_photo` with `granted=false`, the system triggers `erase_biometrics(user_id)`.
   - All rows in `BIOMETRIC_TABLES` are purged and storage purge tasks are enqueued via transactional outbox.
