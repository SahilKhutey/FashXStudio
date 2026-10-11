# Account Deletion & Permanent Erasure Notice

**Self-Service URL**: `https://fashx.studio/account/delete`  
**In-App Navigation**: Profile Screen > Settings > Privacy & Rights > Delete Account  
**Statutory Basis**: DPDP Act 2023, Section 12 (Right to Erasure)  

---

## 1. What Happens When You Request Deletion

When you tap **"Permanently Delete My Account"**:

1. **Biometric & Photo Purge (Immediate)**:
   - Your uploaded body photos, silhouette captures, and skin tone measurements are deleted instantly from our PostgreSQL database and AWS S3 storage buckets (`u/{user_id}/`).
   - Any active virtual try-on jobs in progress are aborted immediately.
2. **Account & Profile Records (Immediate)**:
   - Your user profile, style preferences, size preferences, and wardrobe favorites are permanently removed.
   - Your Supabase login session is revoked across all active devices.
3. **Analytics & Diagnostic Logs**:
   - Historical event logs retain general interaction patterns for statutory recordkeeping, but your unique user identifier is permanently stripped (`user_id = NULL`), severing any link between past events and your identity.
4. **Permanent Erasure Tombstone**:
   - To guarantee that restoring a database backup will never revive your deleted account, a minimal pseudonymous cryptographic record (`user_id`, `erased_at`) is stored in `erasure_tombstones`.

---

## 2. In-App User Dialog Copy

### Confirmation Screen 1:
> **Delete your FashX Account?**  
> This action cannot be undone. All your uploaded photos, body profiles, closet items, and saved looks will be permanently deleted immediately.  
> `[Cancel]` | `[Continue to Delete]`

### Confirmation Screen 2 (Final Warning):
> **Final Confirmation**  
> Are you absolutely sure? Once deleted, you will not be able to recover your virtual closet or uploaded photos.  
> `[Keep My Account]` | `[Permanently Delete Everything]`

---

## 3. Alternative Assistance (Email Submission)

If you cannot access your mobile app or wish to submit an erasure request via email, send a message from your registered account email to:  
`dpo@fashx.studio`  
Subject: `DPDP Section 12 Erasure Request - [Your Registered Email]`  

Our Data Protection Officer will process and verify your request within 72 hours.
