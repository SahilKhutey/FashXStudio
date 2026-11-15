# Shopper Profile Security Test Report

## 1. Security Scope and Controls Evaluated

1. **Mass Assignment Defense**:
   - Tested that client-supplied `user_id`, `id`, `version`, `created_at`, `updated_at` are rejected with HTTP 422 Unprocessable Entity.
   - Status: Enforced via `extra="forbid"` on `ShopperProfileCreate` and `ShopperProfileUpdate`.

2. **Cross-Tenant Isolation**:
   - Tested that User A cannot read or write User B's profile.
   - Endpoint `/api/v1/profile/me` derives user strictly from verified JWT `Principal.user_id`.
   - Status: Enforced via database scoping and JWT principal derivation.

3. **Account Lifecycle Gates**:
   - Disabled accounts (`status="disabled"`) attempting profile operations are blocked with HTTP 403 Forbidden ("Account is disabled").
   - Deletion-pending accounts (`status="deletion_pending"`) attempting profile operations are blocked with HTTP 403 Forbidden ("Account is scheduled for deletion").
   - Status: Verified.

4. **Fail-Closed Authentication**:
   - Requests lacking valid `Authorization: Bearer <token>` fail closed with HTTP 401 Unauthorized.
   - Status: Verified.

5. **Route Snapshot Verification**:
   - All OpenAPI routes match expected snapshots without unauthorized route additions or leaks.
   - Status: Verified.
