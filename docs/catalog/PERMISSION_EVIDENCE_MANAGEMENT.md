# Permission Evidence Management Specification

**Workstream**: 5.1.11 — Legal Evidence Tracking & Audit Verification  
**Status**: Active  
**Database Table**: `catalog_authorization_evidence`

---

## 1. Principles
1. **No Permission Without Evidence**: A catalog source cannot be cleared into the `ACTIVE` state without at least one verified legal authorization document.
2. **Cryptographic Integrity**: Every evidence document stored must have an immutable SHA-256 digest computed at upload time to guarantee provenance and detect tampering.
3. **Traceability**: Every granted permission record in `catalog_source_permissions` points directly to an `evidence_id`.

---

## 2. Evidence Data Schema (`catalog_authorization_evidence`)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | No | Primary key |
| `source_id` | UUID | No | Associated `catalog_sources.id` (Foreign Key) |
| `evidence_type` | String(32) | No | `CONTRACT`, `AMENDMENT`, `EMAIL_CONFIRMATION`, `TERMS_OF_SERVICE`, `AFFILIATE_AGREEMENT` |
| `document_reference` | String(512) | No | S3 object URI or legal document vault reference |
| `document_sha256` | String(64) | Yes | Hex-encoded SHA-256 digest of document file |
| `agreement_reference` | String(255) | Yes | Internal contract reference (e.g. `MSA-2026-IND-042`) |
| `agreement_version` | String(100) | Yes | Version identifier of the contract terms |
| `granted_by_name` | String(255) | Yes | Name of merchant executive executing agreement |
| `granted_by_role` | String(160) | Yes | Role/Title of signatory (e.g. `General Counsel`, `VP Digital`) |
| `verified_by` | UUID | Yes | Internal FashX compliance officer reviewing document |
| `effective_at` | DateTime | Yes | Start date of legal validity |
| `expires_at` | DateTime | Yes | Expiration date of legal validity |
| `verification_status` | String(24) | No | `PENDING`, `VERIFIED`, `REJECTED`, `SUPERSEDED` |
| `created_at` | DateTime | No | System timestamp of record creation |

---

## 3. Evidence Lifecycle

```
[ PENDING ] ---> [ VERIFIED ] ---> [ SUPERSEDED ]
     |
     v
[ REJECTED ]
```

- **PENDING**: Uploaded by onboarding team; pending legal compliance review.
- **VERIFIED**: Compliance officer confirms signature authority, scope matching, and cryptographic hash.
- **REJECTED**: Document rejected due to missing signatures, expired terms, or unauthorized signatory.
- **SUPERSEDED**: Replaced by a newer contract amendment or renewal. Permissions mapped to superseded evidence must be re-evaluated.
