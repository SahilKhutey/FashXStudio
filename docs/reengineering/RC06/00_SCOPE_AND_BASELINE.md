# RC-06 — Scope & Baseline

## Objectives
1. Take FashXStudio from a working Virtual Try-On experience (RC-05) to a complete, verified shopping and purchase handoff journey.
2. Expose real retailer offers with verified pricing in integer minor units (paise for INR), explicit stock status, and real timestamps (`updated_at` from `last_synced_at`, zero fabricated dates).
3. Deliver intelligent multi-offer comparison sorting offers in-stock first, then ascending by price, with the canonical display price computed from the lowest in-stock offer.
4. Enforce strict outbound retailer destination validation: HTTPS protocol strictly required, user credentials rejected, hostname lookalikes rejected, domain suffix allowlist enforced (fails closed in production).
5. Secure purchase handoff via `/commerce/buy-clicks`: require explicit `garment_id` AND `offer_id` (mandatory offer selection; no generic buy fallback), derive user identity strictly from JWT principal, and attach standard affiliate attribution parameters (`utm_source`, `utm_medium`, `utm_campaign`, `sub_id`, `click_id`).
6. Harden cart and checkout endpoints against cross-user ownership tampering while preserving external retailer handoff as the authoritative MVP purchase path.
7. Seamlessly integrate wardrobe save, listing, and removal with accurate snapshot metadata (`snapshot_title`, `snapshot_price_minor`).
8. Modernize Expo mobile application screens (`RetailerOffers.tsx`, `useBuy.ts`, `buyClickApi.ts`, `garment/[id].tsx`) to require explicit offer selection before proceeding to retailer.

## Baseline
- **Base Branch:** `recovery/rc05-vto-integration`
- **Implementation Branch:** `recovery/rc06-shopping-integration`
- **Target Remote:** `origin/recovery/rc06-shopping-integration`

## Scope Boundaries & Commerce Core Principles
- **Decision vs Execution Boundary:** FashX helps users decide what to buy; the external retailer remains responsible for stock, checkout, payment, and order fulfillment.
- **Attribution vs Sale Confirmation:** A buy-click is an outbound handoff / attribution event, NEVER proof of purchase. FashX must never simulate, mock, or emit `purchase_confirmed` without verified affiliate conversion data.
- **Mandatory Offer Selection:** Users cannot initiate a purchase handoff without selecting an explicit retailer offer.
- **No Mock Purchases:** Mock checkouts or simulated retailer carts are strictly forbidden in customer-facing flows.

## Non-Goals (Out of Scope for RC-06)
- Implementing native multi-merchant cart checkout or handling user payment card data (ADR-0001 commerce boundaries remain external handoff).
- Modifying files in `docs/evidence/`, `docs/provenance.md`, or `docs/release/gates.md` (reserved strictly for human founder per `AGENTS.md`).
- Direct pushes or merges to `main`.
