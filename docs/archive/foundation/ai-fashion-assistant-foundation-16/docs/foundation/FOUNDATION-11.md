# AI Fashion Assistant — Foundation 11

## Product Detail & Shopping Decision Layer

Foundation 11 introduces the first detailed product decision surface between discovery and the later try-on/purchase flows.

### Backend

- Product detail now composes canonical garment, image views, merchant offers, and latest enrichment.
- Product images are represented by storage-backed image records; configured object storage converts them into short-lived signed URLs.
- A specific in-stock offer can be selected with `offer_id`.
- `POST /api/v1/catalog/{product_id}/select-offer` validates an offer and returns the same detail contract.
- `POST /api/v1/wardrobe/save/{product_id}` creates an idempotent user save/snapshot using the existing wardrobe aggregate.
- `POST /api/v1/wardrobe/reject/{product_id}` creates the hard feed exclusion used by discovery.

### API contracts

```text
GET  /api/v1/catalog/{product_id}
POST /api/v1/catalog/{product_id}/select-offer
POST /api/v1/wardrobe/save/{product_id}
POST /api/v1/wardrobe/reject/{product_id}
```

### Mobile

- Added catalog API client and product-detail query hooks.
- Added `/product/[id]` Expo Router screen.
- Added offer selection and save/reject actions.
- Feed cards now navigate to product detail.

### Boundaries

Foundation 11 does not yet perform affiliate redirection or create `buy_clicks`; that remains the commerce execution step after a user has selected an offer. The selected offer is the contract boundary that the later buy-handoff feature consumes.

### Verification

- Backend and contract test suite passes.
- Alembic schema remains unchanged in this stage because all required persistence tables already exist.
- Mobile runtime still requires a network-enabled JS environment with installed `node_modules` for TypeScript/Expo runtime verification.
