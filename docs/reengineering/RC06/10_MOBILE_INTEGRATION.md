# RC-06 — Mobile Client Integration

## Frontend Components & Architecture

The mobile shopping journey was upgraded to require explicit retailer offer selection, validate outbound redirect safety on the client device, and provide clear visual feedback for stock status and pricing.

### 1. `RetailerOffers.tsx` (`mobile/src/features/wardrobe/RetailerOffers.tsx`)
- Displays all available retailer offers sorted in-stock first, ascending by price.
- Implements accessible radio button controls (`accessibilityRole="radio"`, `accessibilityState={{ checked: isSelected, disabled: !offer.in_stock }}`).
- Renders retailer merchant name (or `"Authorized Retailer"` fallback).
- Renders formatted prices using `formatOfferPrice(offer.price_minor, offer.currency)`.
- Renders relative sync timestamps if `updated_at` is present.
- Disables out-of-stock offers and marks them with an "Out of Stock" badge.
- Disables the primary CTA button ("Continue to selected retailer") until an offer is explicitly chosen.

### 2. `useBuy.ts` (`mobile/src/features/commerce/useBuy.ts`)
- Calls `createBuyClick({ garment_id, offer_id })`.
- Validates the received `redirect_url` using `isSafeRetailerRedirect(result.redirect_url)` before initiating handoff.
- Opens the validated URL via Expo `Linking.openURL(url)` or falls back cleanly to `WebBrowser.openBrowserAsync(url)`.

### 3. `GarmentDetailScreen` (`mobile/app/garment/[id].tsx`)
- Wires `<RetailerOffers>` directly into the screen body, passing `onBuy={(offerId) => executeBuy({ garment_id: garment.id, offer_id: offerId })}`.
- Replaced the generic "Buy Now" button from the bottom bar. The bottom bar is dedicated to "Save" (Wardrobe) and "✨ Try-On" (Virtual Try-On), while purchase handoff lives inside the retailer offer selection module.

### 4. Client URL Safety Validation (`mobile/src/lib/safeRedirect.ts`)
Hardened against open redirects, malicious schemes, and local loopbacks:
- Requires `https:` protocol.
- Rejects embedded user credentials (`user:pass@host`).
- Rejects localhost, loopbacks (`127.0.0.1`, `::1`), link-local metadata addresses (`169.254.169.254`), and wildcards.
- Enforces approved domain allowlist matching when `allowedHosts` is specified.
