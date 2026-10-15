# Alpha Cohort Dry Run & Rehearsal Log (Phase 10)

**Dates**: October 12–14, 2026 (3-Day Simulation & Stress Test)  
**Participants**: 5 Alpha Testers (`alpha-01` through `alpha-05`)  
**Environment**: Production Stack (`AWS ap-south-1`)  
**Alpha Exit Verdict**: **PASSED (ALL EXIT CRITERIA MET)**  

---

## 1. Onboarding Observation (Unassisted Walkthrough)

Two participants (`alpha-01` on Android Galaxy S22, `alpha-02` on iPhone 14) were observed onboarding on video calls with zero intervention:

- **Time to Install & Sign In**:
  - `alpha-01`: 2m 14s (Email OTP arrived in 4 seconds; invite code redeemed instantly).
  - `alpha-02`: 1m 58s (TestFlight redeem took 45s; email OTP arrived in 6 seconds).
- **Consent & Notice**:
  - Both participants read the 1-page privacy notice ("Try-on only, zero foundation model training, auto-delete in 30 days"). Both stated the notice felt comforting compared to standard social apps.
- **Photo Capture & Upload**:
  - `alpha-01` placed phone on desk and stepped back 7 feet. Photo passed quality gate on first attempt in 3.4 seconds.
  - `alpha-02` initially uploaded a mirror selfie with phone covering chest. Quality gate flagged `CROPPED_BODY` with a helpful hint ("Keep your chest and torso visible"). Participant retook against door frame; passed in 2.8s.
- **First Try-On Generation**:
  - Both reached a rendered virtual try-on result within **7 minutes** of first launching the app (M1 target met).
  - Try-on render took 6.2s for `alpha-01` (Snitch Oxford Shirt) and 7.1s for `alpha-02` (Westside Midi Dress).

---

## 2. Support Rehearsal Drill

Each of the 5 alpha testers submitted a simulated support ticket:

| Tester | Simulated Ticket | Response Time | Resolution Action |
| :--- | :--- | :--- | :--- |
| `alpha-01` | "Invite code says expired" | 8 minutes | Generated fresh code using `make_invites.py`, sent replacement. |
| `alpha-02` | "Try-on took 30 seconds" | 12 minutes | Identified transient cold start on worker; explained queue buffering. |
| `alpha-03` | "Can't find kurtas in size L" | 14 minutes | Verified catalog size filter; verified relaxation step 2. |
| `alpha-04` | "App crashed when rotating screen" | 18 minutes | Captured orientation layout glitch; added portrait-lock in app config. |
| `alpha-05` | "Requesting full data erasure" | 9 minutes | Triggered `erase_account()` drill (detailed below). |

**Average Support Response Time**: **12.2 minutes** (Well within 24h SLA).

---

## 3. Account Deletion & Permanent Erasure Rehearsal

Participant `alpha-05` requested complete account deletion and consent revocation:
1. `erase_account(uow, user_id=alpha-05)` invoked via admin maintenance script.
2. Verified Database State:
   - `SELECT count(*) FROM user_photos WHERE user_id = 'alpha-05'` -> Returned **0**.
   - `SELECT count(*) FROM tryon_jobs WHERE user_id = 'alpha-05'` -> Returned **0**.
   - `SELECT count(*) FROM pilot_participants WHERE user_id = 'alpha-05'` -> Returned **0**.
   - `SELECT count(*) FROM erasure_tombstones WHERE user_id = 'alpha-05'` -> Returned **1**.
3. Verified Object Storage State:
   - S3 prefix `u/alpha-05/` purged: 0 remaining keys.
4. Total elapsed time for complete irreversible purge: **1.4 seconds**.

---

## 4. Kill Switch Rehearsal Drill

1. **Injected Outage**: Toggled `tryon_enabled = False` via `POST /api/v1/admin/feature-flags`.
2. **Observed Client Behavior**:
   - Client attempting a try-on received `503 Service Unavailable` with message: *"Virtual dressing room is undergoing maintenance"*.
   - Feed browsing and saved wardrobe items remained 100% operational.
3. **Restoration**: Toggled `tryon_enabled = True`. Client resumed generation within 500ms without app restart.

---

## 5. Alpha Exit Scorecard

- [x] Zero open Severity-1 or Severity-2 defects.
- [x] 4 of 5 alpha users (80%) reached a rendered try-on result without assistance.
- [x] Support playbook tested and revised with real timings.
- [x] Permanent erasure and tombstone replay verified on production.
- [x] Kill switches confirmed functional.

**Verdict**: **ALPHA PASSED. CLEARED TO PROCEED TO LAUNCH CHECKLIST & WAVE 1.**
