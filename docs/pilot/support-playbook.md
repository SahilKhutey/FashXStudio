# Pilot Support Playbook (Top 10 Scenarios)

**Target SLA**: Initial reply < 12 hours (guaranteed < 24 hours).  
**Channel**: `pilot-support@fashx.studio` & Private WhatsApp Pilot Group.  

---

## 1. Issue: "My invite code says invalid or already used"
- **Root Cause**: Typo in code or participant tapped submit twice triggering concurrency lock.
- **Support Reply**:
  > *"Hi {{Name}}, so sorry for the hassle! We’ve refreshed your invitation. Please try this new single-use code: `{{NEW_CODE}}`. If you copy-paste, ensure there are no trailing spaces."*
- **Engineering Action**: Check `pilot_invites` table. If code has `used_at != NULL` with a different user ID, generate a new code via `python scripts/pilot/make_invites.py --cohort {{cohort}} --channel referral --n 1`.

---

## 2. Issue: "My photo keeps failing the upload check"
- **Root Cause**: Face not clearly visible, lighting too dim, or full body cut off at knees/waist.
- **Support Reply**:
  > *"Hi {{Name}}, our quality check is a bit strict to ensure realistic try-on results. For best results: stand about 6–8 feet from your camera so your full body (head to shoes) is visible, against a well-lit wall with light facing you. Avoid mirror selfies where the phone covers your torso!"*
- **Engineering Action**: Inspect `user_photos.failure_reason` in DB (`BLURRY`, `CROPPED_BODY`, `LOW_LIGHT`).

---

## 3. Issue: "Try-on spinner has been spinning for 2 minutes"
- **Root Cause**: Upstream inference timeout or transient Redis Celery queue delay.
- **Support Reply**:
  > *"Hi {{Name}}, looks like our styling engine hit a brief queue delay on that job! Could you pull-to-refresh on your screen? If it hasn't loaded, tap 'Try Again' and it should complete in under 10 seconds."*
- **Engineering Action**: Query `tryon_jobs WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1`. Check worker logs in CloudWatch. If status is `failed`, verify provider circuit breaker.

---

## 4. Issue: "The feed shows 'No items found in your size'"
- **Root Cause**: Specific category (e.g. XL ethnic kurtas) has low stock or catalog filter gap.
- **Support Reply**:
  > *"Hi {{Name}}, thanks for flagging this! We noticed our current catalog had a temporary stock gap for {{Size}} in that category. We've just expanded our partner feed to pull in 500+ fresh options in your size. Pull down to refresh your feed now!"*
- **Engineering Action**: Run catalog sync for that size bucket; verify relaxation ladder step 3.

---

## 5. Issue: "I didn't receive my 6-digit email sign-in code"
- **Root Cause**: Email delayed in spam/promotions tab or Supabase rate-limited.
- **Support Reply**:
  > *"Hi {{Name}}, please check your Spam or Promotions folder for an email from 'FashX Studio' with subject 'Your sign-in code'. If it's not there after 2 minutes, let us know and we can send a direct magic link!"*
- **Engineering Action**: Check Supabase Auth dashboard log for delivery bounce.

---

## 6. Issue: "I want to delete my photo and account"
- **Root Cause**: User exercising DPDP Section 12 right to erasure.
- **Support Reply**:
  > *"Hi {{Name}}, absolutely. You have complete control over your data. You can tap Settings > Privacy & Rights > Delete Account in the app, or I can immediately trigger permanent erasure right now. Which do you prefer?"*
- **Engineering Action**: If user requests manual deletion, run `python scripts/maintenance/erase_user.py --user-id {{UID}} --reason "USER_REQUEST"`. Confirm S3 prefix empty and tombstone created. Reply with confirmation within 24h.

---

## 7. Issue: "The try-on render made my face/neck look distorted"
- **Root Cause**: Model artifact on draped garment, or posture mismatch.
- **Support Reply**:
  > *"Thank you so much for flagging this {{Name}}! That is exactly why we're running this pilot. We're tuning our boundary-blending weights for this specific garment type. We've credited your account with extra daily try-on credits while we calibrate!"*
- **Engineering Action**: Log feedback in `pilot_feedback(kind='bug')`. Check garment category and pipeline version.

---

## 8. Issue: "App closed unexpectedly while scrolling"
- **Root Cause**: Memory pressure on low-RAM device or unhandled image decode error.
- **Support Reply**:
  > *"So sorry about that crash {{Name}}! Could you let us know which phone model you're using? We've captured the technical crash log and are releasing a memory optimization update within 24 hours."*
- **Engineering Action**: Check Sentry / CloudWatch crash logs. Identify stack trace.

---

## 9. Issue: "I clicked 'Buy on Store' but the merchant site says Out of Stock"
- **Root Cause**: Partner merchant offer price/stock staleness.
- **Support Reply**:
  > *"Thanks for catching that! The merchant just updated their inventory on their site. We've updated our catalog to hide that specific SKU and refreshed similar in-stock alternatives on your feed."*
- **Engineering Action**: Deactivate `merchant_offers` record where `in_stock = False`.

---

## 10. Issue: "Feedback button doesn't open anything"
- **Root Cause**: Modal presentation glitch on older OS.
- **Support Reply**:
  > *"Thanks for letting us know! While we push a quick fix, you can share your feedback, screenshots, or ideas directly right here in this chat anytime!"*
- **Engineering Action**: Push OTA fix via Expo Updates.
