# Merchant Redirect Integration

- `validate_merchant_url()` (`backend/fashx/catalog/detail/redirect_validator.py`) enforces `https`, rejects embedded credentials, rejects lookalike/unlisted domains, and allows only verified merchant domains/subdomains.
- Mobile `onMerchantRedirect()` calls `POST /catalog/offers/{offer_id}/redirect` (`useMerchantRedirect`), validates `https` + `hostname` via `Linking.parse`, and never trusts client-supplied URLs.
