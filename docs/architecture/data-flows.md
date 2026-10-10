# System Architecture: Virtual Try-On Data Flows & Privacy Protection

_Date: 2026-10-10 · Architecture & DPDP / GDPR Compliance Record_

---

## 1. End-to-End Data Pipeline

The Virtual Try-On (VTO) execution pipeline is designed strictly around the **principle of least privilege and zero data exposure**:

```
[User Device]
      │
      │ 1. TLS 1.3 Upload: Portrait photo with explicit consent
      ▼
[API Server]
      │ 2. Strips EXIF/GPS metadata; validates portrait dimensions & contrast
      │ 3. Stores in private storage with prefix u/<user_id>/photos/<photo_id>.jpg
      ▼
[Private Bucket (S3/R2)]
      ▲
      │ 4. Worker claims job via lease, retrieves user photo & catalog garment
      ▼
[GPU / Try-On Worker]
      │ 5. Resize to max 1536px; prepare minimal JPEG payload
      │ 6. Submit via TLS Bearer auth (vendor receives no user ID, no metadata)
      ▼
[External Vendor: FASHN API (tryon-v1.6 / Max)]
      │ 7. Ephemeral GPU inference in memory
      │ 8. Vendor output stored temporarily on vendor CDN (auto-deleted within 72h)
      ▼
[GPU / Try-On Worker]
      │ 9. Download output immediately to worker (no Auth header sent to CDN)
      │ 10. Verify image decodability; apply C2PA provenance watermark
      │ 11. Upload final image to private bucket: u/<user_id>/tryon/<job_id>.jpg
      ▼
[Private Bucket (S3/R2)]
      ▲
      │ 12. Dynamic capability signed URL generated per request (300s TTL)
      ▼
[User Device]  <-- Client NEVER sees vendor URL or permanent storage endpoint
```

---

## 2. Vendor Sub-Processor Information & DPDP Compliance

| Item | Specification |
|---|---|
| **Sub-Processor Name** | FASHN AI Inc. |
| **Function** | Hosted neural virtual try-on inference |
| **Data Transferred** | Ephemeral preprocessed portrait photo & garment image (JPEG bytes only; no name, email, user_id, or EXIF) |
| **Vendor Processing Location** | United States / European Union (Cloudflare / AWS) |
| **Training Use** | **Strictly prohibited** under signed Vendor DPA |
| **Vendor Retention Policy** | Maximum 72 hours on vendor CDN servers; inputs and outputs are purged automatically |
| **User Deletion Procedure** | When user revokes consent or invokes right to erasure, local photos and results are immediately purged. FASHN API jobs expire and purge within 72h (or immediate vendor deletion request via support ticket) |
| **Age Requirement** | **Adults Only (18+)**. Minors / children are strictly barred during the pilot phase in accordance with DPDP regulations |

---

## 3. Data Revocation & Cascading Erasure Safeguards

1. **Pre-Inference Gate:** If consent is revoked before the worker submits to the vendor, the job is immediately cancelled; no external network call is made.
2. **In-Flight Cancellation:** If consent is revoked while the vendor is processing an asynchronous job, the worker discards the returned image upon collection without writing to storage or creating media rows.
3. **Cascading Erasure (Gate G4):** Deleting an account (`DELETE /api/v1/me`) or revoking biometric consent (`POST /profile/{user_id}/consent/revoke`) purges all objects under `u/<user_id>/` from the private bucket.
