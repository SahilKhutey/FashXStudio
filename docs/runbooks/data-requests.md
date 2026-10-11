# Data Principal Rights Request Runbook (DPDP Act 2023)

## 1. Overview & Statutory Scope

Under Chapter III of the Digital Personal Data Protection Act, 2023:
- **Section 11**: Right to access information about personal data (summary of data processed, identities of all data fiduciaries/processors shared with).
- **Section 12**: Right to correction and erasure of personal data.
- **Response SLA**: Mandatory completion within **72 hours** of verified request.

---

## 2. Ingestion & Identity Verification

1. **Request Intake Channels**:
   - In-App self-service: Profile > Account Settings > Privacy & Rights.
   - Email: `privacy@fashx.studio` / `dpo@fashx.studio`.
2. **Verification Protocol**:
   - For in-app requests: Authenticated via active session token.
   - For email requests: User must verify ownership by confirming a one-time cryptographic magic link sent to their registered Supabase email address. Never process requests from unverified third-party addresses.

---

## 3. Execution Procedures

### A. Right to Access / Data Export (DPDP Section 11)
To generate an end-to-end data package for a verified user:
1. Export profile attributes, preferences, wardrobe items, and fit feedback:
   ```bash
   GET /api/v1/me/export (authenticated endpoint)
   ```
2. The endpoint gathers:
   - Profile metadata and size preferences (`user_style_profiles`, `body_profiles`).
   - Wardrobe snapshots (`wardrobe_items`).
   - Feed interaction history (`feed_signals`).
   - Third-party data processors list: Supabase (Auth), AWS ap-south-1 (Cloud/Storage), FASHN AI (Try-on processing).
3. Deliver encrypted JSON package to the user's verified email.

### B. Right to Erasure / Account Deletion (DPDP Section 12)
1. **Self-Service Deletion**:
   - Calling `DELETE /api/v1/me` invokes `erase_account(uow, user_id, storage)`.
2. **Operator Deletion (via DPO CLI)**:
   ```bash
   python scripts/maintenance/erase_user.py --user-id <UUID> --reason "DPDP_S12_REQUEST"
   ```
3. **What `erase_account` does**:
   - Instantly cascades deletion across all biometric tables (`media_objects`, `user_photos`, `body_profiles`, `tryon_jobs`).
   - Purges S3 object prefix `u/{user_id}/`.
   - Strips `user_id` from analytics logs (`UPDATE domain_events SET user_id = NULL`).
   - Deletes all user account records.
   - Inserts pseudonymous tombstone into `erasure_tombstones(user_id, erased_at)` to prevent accidental recreation on backup restore.
   - Logs `pd_access` audit event with actor, timestamp, and purpose.
4. Issue completion confirmation email to the user within 72 hours.
