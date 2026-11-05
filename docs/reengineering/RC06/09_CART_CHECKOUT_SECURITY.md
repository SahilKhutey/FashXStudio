# RC-06 — Cart & Checkout Security Hardening

## Overview & Tasks (RC06-T19 & RC06-T20)

While the authoritative purchase path for the MVP remains external retailer redirection, existing auxiliary endpoints under `/api/v1/customer/cart` and `/api/v1/checkout` were audited and hardened to prevent cross-user data exposure or privilege escalation.

### 1. Customer Cart Ownership Enforcement (RC06-T19)
- **Path:** `backend/fashx/api/v1/cart.py`
- **Issue:** Previously, `get_customer_cart`, `add_cart_item`, and `remove_cart_item` accepted a `customer_id` path parameter without validating whether the caller's JWT principal matched that `customer_id`.
- **Hardening:**
  ```python
  if customer_id != principal.user_id and principal.role != "admin":
      raise ApiError(status_code=status.HTTP_403_FORBIDDEN, message="Forbidden: cannot access another customer's cart")
  ```

### 2. Checkout Session Ownership Scoping (RC06-T20)
- **Path:** `backend/fashx/api/v1/checkout.py`
- **Issue:** `get_checkout_session` returned session details for any session ID without verifying that the session belonged to the authenticated principal.
- **Hardening:**
  ```python
  session = await service.get_session(session_id)
  if not session:
      raise EntityNotFoundError("CheckoutSession", session_id)
  if session.customer_id != principal.user_id and principal.role != "admin":
      raise ApiError(status_code=status.HTTP_403_FORBIDDEN, message="Forbidden: cannot access another customer's checkout session")
  ```

### Verification Evidence
Tested under `tests/integration/test_rc06_user_isolation.py::test_rc06_cart_and_checkout_user_isolation`:
- Verified User B receiving 403 Forbidden when requesting User A's cart.
- Verified User B receiving 403 Forbidden when attempting to retrieve User A's checkout session.
