# FashXStudio — Personal Data Inventory & Classification

## 1. Regulatory Context
In compliance with the **Digital Personal Data Protection (DPDP) Act 2023 (India)** and **General Data Protection Regulation (GDPR)**, this document classifies all data elements stored, processed, and transmitted across FashXStudio services.

---

## 2. Table Classification Matrix

### 2.1 Biometric & Sensitive Personal Data (`BIOMETRIC_TABLES`)
These tables contain user body photographs, inferred facial/pose landmarks, skin tone measurements, and 3D mesh artifacts. Under DPDP Act 2023, these are classified as sensitive personal data requiring heightened security controls, zero-knowledge storage keys, and instant cascade on consent revocation.

| Table Name | Description | Retention Period | Deletion Behavior |
| :--- | :--- | :--- | :--- |
| `user_media` | User-uploaded photos and validated WebP images | Active consent / 30-day max staging | Immediate cascade & S3 prefix purge |
| `media_uploads` | Upload session tracking and quarantine tokens | 1 hour upload TTL / 24 hour purge | Hard-delete on session expiry |
| `user_photos` | Historical legacy profile photos and pose scores | Active account / Revocation | Hard-delete on consent revocation |
| `tryon_jobs` | ML virtual try-on execution jobs and artifact keys | 90 days or until user deletion | Hard-delete |
| `profile_artifacts` | Generated virtual try-on composite images | 90 days or until user deletion | Hard-delete & S3 object purge |
| `profile_photo_jobs` | Background image validation and pose extraction | 7 days | Hard-delete |
| `skin_tone_results` | Colorimetric skin-tone and undertone analysis | Active account | Hard-delete |
| `body_profiles` | Inferred 3D anthropometric landmarks | Active account | Hard-delete |
| `user_measurements` | Detailed measurement series (chest, waist, inseam) | Active account | Hard-delete |
| `user_style_profiles` | Machine-learned style embeddings | Active account | Hard-delete |

### 2.2 Account Personal Data (`ACCOUNT_TABLES`)
General user account state, preferences, shopping activity, and consent history.

| Table Name | Description | Retention Period | Deletion Behavior |
| :--- | :--- | :--- | :--- |
| `shopper_profiles` | User-entered height, weight, fit, style preferences | Active account | Hard-delete on account erasure |
| `profile_category_sizes`| Preferred clothing size per garment category | Active account | Hard-delete on account erasure |
| `profile_measurements` | Explicit physical measurements entered by shopper | Active account | Hard-delete on account erasure |
| `identity_accounts` | Provider subject mapping (`(provider, provider_sub)`) | Active account | Hard-delete on account erasure |
| `auth_sessions` | Active JWT session JTI tracking and device labels | Token lifetime | Hard-delete on account erasure |
| `consent_records` | Current consent state for legal processing | Active account | Hard-delete on account erasure |
| `consent_events` | Immutable log of consent grant/revocation events | Active account | Hard-delete on account erasure |
| `wardrobe_items` | Garments saved or purchased by shopper | Active account | Hard-delete on account erasure |
| `fit_feedback` | User fit evaluations on purchased/tried garments | Active account | Hard-delete on account erasure |
| `tryon_feedback` | User qualitative feedback on try-on generation | Active account | Hard-delete on account erasure |
| `feed_exclusions` | Items hidden or dismissed from personal discovery | Active account | Hard-delete on account erasure |
| `feed_impressions` | Impression logs for personalized ranking | 30 days rolling | Hard-delete on account erasure |
| `product_search_events` | Search interactions, clicks, and queries | 30 days rolling | Hard-delete on account erasure |
| `search_sessions` | Search session tokens, cursors, and filter states | Session lifetime | Hard-delete on account erasure |

### 2.3 Anonymized Operational Logs (`ANONYMIZE_TABLES`)
Records where personal identification is decoupled while preserving aggregate statistical trends.

| Table Name | Description | Action on User Erasure |
| :--- | :--- | :--- |
| `domain_events` | Asynchronous system domain event stream | `user_id` set to `NULL` |
| `pilot_invites` | Beta pilot onboarding attribution codes | `user_id` set to `NULL` |

### 2.4 Minimal Retained Tombstones (`RETAINED_MINIMAL`)
Cryptographically minimal pseudonymous records retained strictly to prevent zombie account resurrection during database backup restorations.

| Table Name | Retained Fields | Justification |
| :--- | :--- | :--- |
| `erasure_tombstones` | `user_id`, `erased_at` | Rule 9.8 / GDPR Art. 17: Prevents resurrecting erased user if backup is restored. Contains no personal data. |
| `account_deletion_jobs` | `id`, `user_id`, `status`, `requested_at`, `completed_at` | Audit verification of completed erasure workflows. |

---

## 3. Storage Key Hierarchy (`fashx-media-private`)

- **Quarantine Prefix**: `u/{user_id}/quarantine/{token}/` (Presigned PUT destination, strictly non-public, lifecycle expiration 24 hours).
- **Normalized Media Prefix**: `u/{user_id}/photos/{media_id}.webp` (Stripped EXIF, normalized format, signed URL download only).
- **Purge Invariant**: Deletion of user account or revocation of `body_photo` consent purges the entire S3 prefix `u/{user_id}/` immediately and durability-verified via Celery purge tasks.
