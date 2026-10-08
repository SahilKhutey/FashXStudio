# FashXStudio - Honest Status

_Last updated: 2026-10-04. Update this file in every milestone PR. If a claim is not in this table, it is not claimed._

**Product (MVP):** AI styling + discovery + virtual try-on, with affiliate redirect to merchants.
**Stage:** Pre-pilot. Architecture and contracts are strong; most runtime integrations are mocked.

Legend: ✅ real and tested · 🟡 partial / mocked · ⬜ not started · ❄️ frozen (post-MVP)

## MVP scope

| Area | Status | Notes |
|---|---|---|
| Profile + photo quality gate | 🟡 | Logic and tests exist; needs real image fixtures and real storage (R2/S3) |
| Skin tone (Monk) calibration | 🟡 | Tested on synthetic data; not validated on real faces |
| Consent + cascading erasure | 🟡 | Implemented; needs DPDP legal review |
| Catalog ingest + dedup + normalization | 🟡 | Logic exists; no legitimate live data source connected |
| VLM attribute enrichment + embeddings | 🟡 | Interface exists; accuracy not measured on real catalog |
| 3-stage discovery feed | 🟡 | Works on test data; not evaluated with real users |
| Virtual try-on job lifecycle | 🟡 | Async 202 flow + cache done; runs on `MockAdapter` |
| Try-on model (license-cleared) | ⬜ | Blocking: research weights not allowed in production (I08 / G5) |
| GPU worker connected | ⬜ | Contracts only |
| Closet + price snapshot | 🟡 | Domain done; verify persistence |
| Affiliate redirect + sub-IDs | 🟡 | URL generation done; no live affiliate program |
| Fit feedback ledger | 🟡 | Needs real outcome data (cold start) |
| Authentication + ownership checks | ⬜ | Blocking: routes take `{user_id}` in path |
| PostgreSQL persistence (MVP domains) | 🟡 | Verify all MVP repos use Postgres, not in-memory |
| Mobile app (4 core screens) | ⬜ | Expo scaffold exists; screens not bound to real API |
| CI (lint, mypy, tests, migrations) | ⬜ | Verify workflows run all four on every PR |

## Frozen (post-MVP, do not extend)

| Area | Status | Why |
|---|---|---|
| Inventory, warehouses (C05) | ❄️ | We redirect to merchants; we hold no stock |
| Promotions engine (C06) | ❄️ | Merchant-side concern |
| Own cart / checkout / orders (C07-C08) | ❄️ | Replaced by affiliate redirect |
| Payments (C09) | ❄️ | No payment capture in MVP |
| Fulfillment, returns (C10-C11) | ❄️ | Merchant-side concern |
| Regional, social/engagement (F12-F13) | ❄️ | Revisit after pilot |

## Release gates (real status)

| Gate | Status | Blocker |
|---|---|---|
| G1 Functional | 🟡 | E2E runs on mocks only |
| G2 ML quality | ⬜ | Needs real models + labeled sample |
| G3 Performance | ⬜ | Needs real GPU + load test |
| G4 Privacy | 🟡 | Tests exist; needs legal review |
| G5 Commercial clearance | ⬜ | No license-cleared try-on model selected |
| G6 User acceptance | ⬜ | No pilot yet |

## Known debt
- Possible package-name collision: root `app/` vs `api/app/` (see RESTRUCTURE_GUIDE.md).
- Duplicate mobile dirs (`mobile/` vs `apps/mobile`).
- Test and migration counts differ between docs (1271 vs 663 tests; 12 vs 13 migrations): take numbers from CI, not prose.
