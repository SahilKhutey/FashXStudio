# API Integration Contract

All mobile requests pass through `mobile/src/api/client.ts` against `/api/v1`.

| Feature | Method & Path (Mobile Client) | Backend Mounted in `create_app()` | Contract Status |
|---|---|---|---|
| Current User | `GET /api/v1/me` | Yes | Aligned |
| Profile Update | `PATCH /api/v1/profile/me` | Yes | Aligned |
| Fit Measurements | `POST /api/v1/profile/fit/measurements` | Yes | Aligned |
| Onboarding Progress | `GET /api/v1/onboarding/progress` | No (`style-quiz` mounted) | Open Gap (`BUG-09-03`) |
| Search Catalog | `GET /api/v1/search/products` | Yes | Aligned |
| Shopper Feed | `GET /api/v1/feed` | Yes | Aligned |
| Product Detail | `GET /api/v1/catalog/products/{product_id}/detail` | No (`catalog/detail/router.py` unmounted) | Open Gap (`BUG-09-01`) |
| Merchant Redirect | `POST /api/v1/catalog/offers/{offer_id}/redirect` | No (`catalog/detail/router.py` unmounted) | Open Gap (`BUG-09-01`) |
| Submit / Poll VTO | `POST/GET /api/v1/tryon/jobs` | Yes | Aligned |
| Wardrobe Items | `GET/POST/DELETE /api/v1/wardrobe/items` | Yes | Aligned |
| Saved Looks | `GET/POST/DELETE /api/v1/wardrobe/looks` | No (`looks/router.py` unmounted) | Open Gap (`BUG-09-02`) |
