# Profile Ownership and Authorization

## 1. Zero-Trust Identity Binding
1. **No Client-Supplied Identifiers**:
   - The profile endpoints operate exclusively on `/api/v1/profile/me`.
   - The user ID is retrieved directly from the verified cryptographic JWT bearer token (`Principal.user_id`).
   - If a client supplies a `user_id` inside the request body, Pydantic's `extra="forbid"` rule rejects the request with HTTP 422 Unprocessable Entity.

2. **Cross-Tenant Isolation**:
   - Every database query in `ShopperProfileRepository` filters explicitly by `ShopperProfile.user_id == user_id`.
   - Shopper A can never read, modify, or infer the existence of Shopper B's profile.

## 2. Account Status Lifecycle Enforcement
The profile service coordinates with `AccountRepository` on every operation to verify account health:

| Account Status | Action on Profile API Request |
| :--- | :--- |
| `ACTIVE` | Allowed. Full read and write access. |
| `PENDING_VERIFICATION` | Allowed. User can set initial sizing before email verification. |
| `DISABLED` | Blocked. Raises `HTTP 403 Forbidden` ("Account is disabled"). |
| `DELETION_PENDING` | Blocked. Raises `HTTP 403 Forbidden` ("Account is scheduled for deletion"). |
| `DELETION_IN_PROGRESS`| Blocked. Raises `HTTP 403 Forbidden`. |
| `DELETED` | Blocked. Raises `HTTP 403 Forbidden`. |
| Not Found in `users` | Blocked. Raises `HTTP 404 Not Found`. |
