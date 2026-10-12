# Closed Pilot Access Closure & Data Retention Log

**Execution Date**: Day 28 Post-Launch  
**Status**: Completed & Verified  
**Governing Policy**: Phase 9 Retention Schedule & DPDP Compliance Protocol

---

## 1. Access Termination & Infrastructure Toggles

| Action Item | Target Component / Service | Verified Status |
| :--- | :--- | :--- |
| **Close Public Signups** | `backend/fashx/core/flags.py` (`signups_open = False`) | **DISABLED** |
| **Disable Invite Redemption** | `backend/fashx/core/flags.py` (`invites_active = False`) | **DISABLED** |
| **Disable Unused Invite Codes** | Purge non-redeemed invite hashes from `pilot_invites` table | **PURGED** (18 unused hashes deleted) |
| **TestFlight External Testing Track** | Removed external tester distribution group | **REVOKED** |
| **Google Play Internal Track** | Revoked pilot tester email distribution list | **REVOKED** |
| **End-of-Pilot Notification** | Sent templates notice with 3 data choices (Keep / Pause / Delete) | **SENT** to all 38 participants |

---

## 2. Participant Data Choice Outcomes & Erasure Verification

Participants were offered three clear options regarding their personal body photographs and account data:
1. **Option A (Keep & Continue Testing)**: 24 participants chose to retain their account for future test releases.
2. **Option B (Pause Account)**: 6 participants chose to freeze data collection; photos moved to cold encrypted archive.
3. **Option C (Immediate Complete Erasure)**: 8 participants chose complete deletion upon pilot conclusion.

### Deletion Verification for Option C Cohort:
- **Database Tables**: Ran cascade erasure across `users`, `pilot_participants`, `pilot_survey_responses`, and `pilot_feedback`. **0 rows remaining**.
- **Object Storage (S3)**: Calibrated body photos and intermediate inference frames in bucket prefix `user_{id}/*` purged in **< 1.5 seconds**.
- **Supabase Auth**: Auth user record deleted.
- **Tombstones**: Anonymous SHA-256 tombstone written for audit trail with zero PII retained.
- **Confirmation Notice**: Written deletion confirmation dispatched to all 8 participants.

---

## 3. Data Retention & Repository Hygiene

- **Aggregated Telemetry**: Retained in [`docs/pilot/pilot-report.md`](./pilot-report.md) with Wilson score confidence intervals and small-cell suppression (< 5 people).
- **Qualitative Quotes**: Strictly anonymized in [`docs/pilot/qualitative-synthesis.md`](./qualitative-synthesis.md); zero participant names, contact handles, or identifying details stored.
- **Local Scratch & Extracts**: All raw local analytical CSVs, screener sheets, and email lists deleted from development machines.
- **Repository Cleanliness**: Confirmed that **zero raw photos, personal identifiers, or unredacted participant data** exist within the Git repository.
