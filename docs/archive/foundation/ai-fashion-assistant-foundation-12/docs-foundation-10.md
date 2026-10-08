# AI Fashion Assistant — Foundation 10

## Catalog Feed & Discovery Runtime

Foundation 10 adds the first user-facing discovery runtime over the curated MVP catalog.

### Scope

- deterministic curated feed
- newest-first ordering with UUID tie-break
- opaque cursor pagination
- category/subcategory filtering
- price-range filtering
- in-stock filtering
- hard exclusion support through `feed_exclusions`
- feed reason labels for UI/debugging
- lightweight mobile feed using TanStack Query infinite pagination
- no ML ranking, CLIP ranking, fit scoring, or personalization model yet

### API

`GET /api/v1/feed/me`

Query parameters:

- `category`
- `subcategory`
- `price_min`
- `price_max`
- `limit` (1–50)
- `cursor`

The authenticated user is taken from the auth dependency; the client does not provide a user ID.

### Ordering

The MVP feed is deliberately deterministic:

`created_at DESC, garment_id DESC`

This provides a stable new-arrival/curated ordering without pretending that recommendation intelligence exists before the validation data exists.

### Pagination

The cursor encodes the last `(created_at, garment_id)` pair in URL-safe base64 JSON. Cursors are opaque to mobile clients and invalid cursors return HTTP 400.

### Mobile

The mobile feed uses `useInfiniteQuery()` and loads additional pages on scroll. Server state remains in TanStack Query; no feed copy is kept in Zustand.

### Explicitly deferred

- color-harmony ranking
- style-vector ranking
- fit-score ranking
- learned recommendation models
- dedicated search engine
- multi-source ranking
