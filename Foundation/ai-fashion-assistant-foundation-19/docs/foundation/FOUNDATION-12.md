# AI Fashion Assistant — Production Build Foundation 12

## Commerce & Buy-Handoff

### Goal
Establish the MVP commerce boundary between a selected merchant offer and an outbound shopping redirect, with attribution and immutable `buy_clicked` domain-event recording.

### Implemented
- `POST /api/v1/commerce/buy-click`
- Merchant URL is sourced only from the trusted catalog offer; clients cannot supply a redirect destination.
- Configured affiliate adapter appends a configurable tracking parameter and source marker.
- `buy_clicks` records user, garment, offer, affiliate network, and tracking ID.
- `buy_clicked` is persisted as a domain event in the same transaction.
- Optional `Idempotency-Key` is supported for repeated client submits.
- Existing catalog/offer validation is reused.

### Security
- Invalid merchant destination schemes are rejected.
- User identity is derived from the authenticated request dependency.
- No raw affiliate credentials or merchant URLs are accepted from the client.
- The redirect adapter is replaceable; merchant-specific affiliate networks remain future adapters.

### Architecture
```text
Mobile
  ↓
POST /api/v1/commerce/buy-click
  ↓
Commerce Application Service
  ├── Catalog Offer validation
  ├── AffiliateProvider
  ├── BuyClick persistence
  └── buy_clicked event persistence
  ↓
Trusted merchant redirect
```

### Configuration
- `AFFILIATE_NETWORK=mvp`
- `AFFILIATE_TRACKING_PARAM=afa_click_id`
- `AFFILIATE_SOURCE_PARAM=afa_source`

These are deliberately generic MVP settings. A real network should be introduced through a dedicated adapter after its commercial/affiliate contract is confirmed.

### Migration
No new database migration is required for Foundation 12 because `buy_clicks` and `domain_events` were already established by the prior schema foundations.

### Verification
- Full pytest suite: 61 passed
- Python compilation: passed
- Alembic offline migration generation: passed
- API route registration: passed
- `git diff --check`: passed
- Ruff/mypy were not executable in the current environment because their binaries are unavailable.
