# RC-03 — Shopping & Commerce Integration

## Commercial Boundary (ADR-0001)
FashXStudio operates on an affiliate handoff model. Payment processing, cart management, and inventory handling remain within merchant partner domains.

## Security & Redirect Hardening (Rule I12)

### Backend Validation
`CreateBuyClickUseCase` enforces:
1. Strict HTTPS protocol (`scheme == "https"`).
2. Non-empty hostname with credential rejection (`username` or `password` forbidden).
3. Retailer hostname whitelist verification against `settings.parsed_retailer_allowed_hosts` (`myntra.com`, `amazon.in`, `flipkart.com`, `merchant.com`, `shop.example.com`, `example.com`).
4. Attribution tracking injection: generates unique `tracking_id` (`fashx_{user_prefix}_{uuid}`) and appends UTM campaign parameters.

### Mobile Client Validation
The client implementation in `mobile/src/lib/safeRedirect.ts` enforces identical safeguards before opening external system browsers:
- Validated via `isSafeRetailerRedirect(url, allowedHosts?)`.
- Integrated into `useBuy` (`mobile/src/features/commerce/useBuy.ts`) and `RetailerOffers` (`mobile/src/features/wardrobe/RetailerOffers.tsx`).
- Unit tested across 8 edge cases in `mobile/src/lib/__tests__/safeRedirect.test.ts`.
