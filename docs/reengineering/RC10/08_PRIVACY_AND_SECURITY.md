# RC10-H: Privacy, Security and Data Lifecycle

## 1. Objectives
Maintain privacy-by-design, tenant/user isolation, cryptographically signed pre-signed URLs, and rigorous right-to-erasure workflows across all storage layers.

## 2. Invariants & Controls
1. **User Photo & Artifact Isolation**:
   - Access to user profile photos and try-on output artifacts is strictly guarded by ownership checks (`test_ownership.py` and `test_rc10_privacy_regression.py`).
   - S3 and local storage keys are organized under hashed user paths: `photos/{user_id}/{photo_id}`.
2. **Right to Erasure (GDPR / DPDP)**:
   - Account deletion triggers synchronous recording of an `erasure_tombstones` entry.
   - Profile photos, measurements, preference records, and generated try-on artifacts are pruned from storage and database.
   - Future requests referencing erased user IDs fail closed with HTTP 404/410.
3. **Signed Storage URLs**:
   - Direct public access to S3 object storage is disabled. Media downloads and uploads utilize short-lived HMAC pre-signed URLs ($\le 15\text{ minutes}$).
4. **Automated Security Scans**:
   - Gitleaks secrets audit on every PR.
   - Bandit security vulnerability AST scanning.
   - OWASP dependency checking via pip-audit.
