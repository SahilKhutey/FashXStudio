# Storage and Erasure Architecture

## 1. Object Storage Architecture
FashX Studio separates relational metadata (stored in PostgreSQL) from binary media objects (stored in private S3/R2 object storage) adhering strictly to **Rule I06** (*Database holds metadata, the bucket holds bytes*).

### 1.1 Bucket Strategy
- **Cloud Providers:** Cloudflare R2 (zero egress fees, primary production target) / AWS S3 (`ap-south-1` Mumbai data residency alternative).
- **Security Posture:** 100% private buckets (`fashx-media-dev`, `fashx-media-prod`).
- **No Public Domains:** No direct CDN or public URLs are mapped to raw bucket storage.
- **Signed Capability URLs:** All client reads receive expiring presigned capability URLs (default TTL: 300 seconds / 5 minutes) generated on demand.

### 1.2 Object Key Layout
Object keys follow a deterministic, single-function hierarchy (`media_key(user_id, kind, media_id)`):
- **User Reference Photos:** `u/<user_id>/photos/<media_id>.jpg`
- **Virtual Try-On Output Renders:** `u/<user_id>/tryon/<job_id>.jpg`
- **Catalog Garment Assets:** `catalog/garments/<garment_id>.jpg`
- **Ephemeral Scratch:** `tmp/<random>.bin` (governed by 24h bucket lifecycle rule)

### 1.3 Local Developer Workflow
The `LocalStorage` adapter writes objects under `./.local_storage/` (gitignored) and issues cryptographically signed URLs targeting `http://127.0.0.1:8000/dev-files/<key>?exp=<timestamp>&sig=<hmac>`. In production (`ENV=prod`), construction of `LocalStorage` is strictly prohibited by runtime assertion.

---

## 2. Table Classification & Right to Erasure

In compliance with India's DPDP Act and GDPR, every PostgreSQL table containing a `user_id` column is categorized into an explicit erasure class:

| Classification | Purpose / Treatment | Tables |
| :--- | :--- | :--- |
| **Biometric Tables** | Hard-deleted instantly on consent revocation (`erase_biometrics`) or account deletion (`erase_account`). | `media_objects`, `user_photos`, `body_profiles`, `user_measurements`, `user_style_profiles`, `tryon_jobs`, `profile_photo_jobs`, `profile_artifacts`, `skin_tone_results` |
| **Account Tables** | Retained while consent is revoked; hard-deleted completely upon account deletion (`erase_account`). | `wardrobe_items`, `buy_clicks`, `fit_feedback`, `tryon_feedback`, `feed_exclusions`, `user_preferences`, `onboarding_profiles`, `consent_records`, `idempotency_records`, `users` |
| **Anonymize Tables** | Append-only event logs; `user_id` is nulled out (`SET user_id = NULL`) upon account deletion. | `domain_events`, `analytics_events` |
| **Auth Identities** | Identity provider mapping; hard-deleted upon account deletion. | `auth_identities` |

---

## 3. Asynchronous Erasure Pipeline (Gate G4 & Rule I16)

Object store deletion can encounter intermittent network or rate limit failures. The erasure engine uses the transactional **Outbox Pattern** to ensure zero residual data:

```
[Client] ---> POST /profile/{user_id}/consent/revoke (202 Accepted)
                    |
                    v
    [PostgreSQL Transaction]
      1. UPDATE consent_records SET granted = FALSE
      2. DELETE FROM biometric_tables WHERE user_id = :uid
      3. INSERT INTO outbox_messages (topic: "storage.delete_prefix", payload: "u/<user_id>/")
                    | (Commit)
                    v
    [Outbox Worker] ---> storage.delete_prefix("u/<user_id>/")
                    |
                    v
    [HMAC Audit] ------> erasure_audit (HMAC hash only, zero PII)
```

### 3.1 Orphan Sweep Worker
The maintenance script `scripts/maintenance/sweep_orphans.py` runs as a daily background task to detect and delete any storage keys under `u/` that lack corresponding database rows in `media_objects` or `user_photos`. This prevents storage bloat from aborted transactions or transient network disconnects.
