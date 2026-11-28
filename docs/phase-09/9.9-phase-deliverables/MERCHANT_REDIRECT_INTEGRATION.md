# Merchant Redirect Integration

- **Backend URL Validation**: `validate_merchant_url(candidate_url, verified_hosts)` (`backend/fashx/catalog/detail/redirect_validator.py`) rejects empty URLs, non-HTTPS schemes (`http://`, `javascript:`), embedded credentials, localhost/private hosts, and unverified domains.
- **Mobile Flow**: `requestMerchantRedirect(offerId)` (`mobile/src/features/product-detail/api.ts`) calls `POST /catalog/offers/{offerId}/redirect` and receives a validated outbound `redirect_url`.
- **Verification**: Covered by `tests/unit/catalog/test_phase09_5_pdp_redirect.py`, `tests/unit/phase_09/test_phase09_exit_gate.py`, and `mobile/__tests__/phase09_9_exit_gate.test.tsx`. Staging router mounting in `main.py` remains open (`BUG-09-01`).
