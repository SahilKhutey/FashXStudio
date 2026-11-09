# RC13: Privacy, Security & Legal Compliance

## 1. Compliance Mandates: India DPDP Act 2023
- **Explicit Consent**: Granular consent requested prior to camera access or photo upload.
- **Purpose Limitation**: User images are strictly utilized for rendering the requested virtual try-on and are never used for model training or shared with third parties.
- **Right to Erasure**: Full account and image deletion capability available via `/api/v1/auth/delete-account`.
- **Zero Biometric Data**: No facial recognition landmarks, biometric templates, or physical measurements (height, weight, body dimensions) are extracted or persisted.

## 2. Infrastructure Security
- **Quarantine and Signed URLs**: Raw photos are uploaded directly to private S3 buckets via short-lived pre-signed URLs (15-minute expiry).
- **Zero PII Logging**: Log scrubbers remove tokens, email addresses, phone numbers, and image payloads from application logs.
- **Automated Quarantine Verifier**: Validated by [`scripts/rc13/validate_evidence.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/validate_evidence.py).
