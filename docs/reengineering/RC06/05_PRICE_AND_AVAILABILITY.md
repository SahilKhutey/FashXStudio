# RC-06 — Price Representation & Freshness Availability

## Minor Unit Currency Standards

To prevent floating-point rounding errors and precision degradation across databases, APIs, and client rendering, all prices in FashX are stored, processed, and transmitted strictly in integer minor units.

| Currency Code | Minor Unit | Divisor | Example Minor | Display Output |
|---|---|---|---|---|
| `INR` | Paisa | 100 | `179900` | `₹1799` |
| `INR` | Paisa | 100 | `179950` | `₹1799.50` |
| `USD` | Cent | 100 | `4999` | `$49.99` |
| `EUR` | Cent | 100 | `3500` | `€35.00` |
| `GBP` | Penny | 100 | `2500` | `GBP 25.00` |
| `JPY` | Sen | 100 | `100000` | `JPY 1000.00` |

### Formatting Rules (`formatOfferPrice` in `mobile/src/features/wardrobe/RetailerOffers.tsx`)
1. For `INR`: If the amount divided by 100 is an exact integer, render with zero decimal places (e.g., `₹1799`). If fractional, render with 2 decimal places (e.g., `₹1799.50`).
2. For `USD` and `EUR`: Render with currency symbols (`$` / `€`) and 2 decimal places.
3. For all other currencies: Prefix with uppercase ISO currency code and 2 decimal places.

### Negative Price Prevention
Negative prices are invalid in commercial fashion catalogs and are rejected at the Pydantic schema validation layer:
```python
price_minor: int = Field(ge=0, description="Price in integer minor units")
```

### Offer Freshness (`updated_at`)
Every `MerchantOffer` record tracks `last_synced_at` from the retailer feed synchronization engine. When serialized in `CustomerOfferDetail`, this timestamp is exposed as `updated_at`:
- If `last_synced_at` is set, its ISO 8601 UTC timestamp is serialized.
- If not yet synced, `updated_at` is `null`.
- Synthetic dates (such as `datetime.now()` or fabricated past dates) are strictly prohibited.
