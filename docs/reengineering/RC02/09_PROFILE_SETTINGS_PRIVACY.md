# RC-02 — Profile, Settings & Privacy Experience

## Architecture & Integration
The Settings screen ([`mobile/app/settings/index.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/app/settings/index.tsx)) enforces privacy and identity standards.

## Key Controls & Backend Operations
1. **Reference Photo Management**:
   - Displays active reference photo status (accepted, pending, rejected).
   - Allows users to view or permanently delete their reference photo via `DELETE /api/v1/profile/{user_id}/photos/{id}`.
2. **Body Photo Consent Controls (DPDP Compliance)**:
   - Provides explicit consent status.
   - Allows immediate consent revocation via `POST /api/v1/profile/{user_id}/consent/revoke`, immediately cancelling pending jobs and purging stored photos.
3. **Account Erasure & Right to Be Forgotten**:
   - Provides account erasure with confirmation alert.
   - Calls `DELETE /api/v1/profile/{user_id}/account`.
   - Purges local session tokens and redirects to sign-in.
4. **Sign Out**:
   - Secure sign-out invalidating React Query caches and clearing local tokens.
