# RC-06 — Retailer Offer Comparison & Ranking

## Ranking Engine Specification

When a customer views a garment detail screen, multiple retailers may stock the identical canonical garment. FashX provides an objective, transparent comparison engine designed to surface the best actionable deal for the customer.

### Sorting Priority
1. **Primary Sort Key (`in_stock`)**: In-stock offers (`in_stock is True`) are always placed before out-of-stock offers (`in_stock is False`). Customers should never be presented with an out-of-stock offer as their primary purchase option.
2. **Secondary Sort Key (`price_minor`)**: Among offers with identical stock status, offers are sorted ascending by price (`price_minor`).
3. **Display Price Resolution**:
   - If one or more in-stock offers exist, `display_price` is set to the lowest in-stock offer price.
   - If all offers are out of stock, `display_price` falls back to the lowest offer price.
   - If no offers exist, `display_price` falls back to the canonical garment's display price.

### Code Implementation (`backend/fashx/catalog/customer_router.py`)
```python
# Sort offers: in-stock first, then ascending by price
sorted_offers = sorted(
    offers,
    key=lambda o: (not getattr(o, "in_stock", True), getattr(o, "price_minor", 0)),
)

# Compute display price
in_stock_offers = [o for o in sorted_offers if getattr(o, "in_stock", True)]
if in_stock_offers:
    display_price = min(getattr(o, "price_minor", 0) for o in in_stock_offers)
elif sorted_offers:
    display_price = min(getattr(o, "price_minor", 0) for o in sorted_offers)
else:
    display_price = getattr(garment, "display_price", 0)
```

### Verification Evidence
Tested under `tests/unit/test_rc06_offer_validation.py`:
- `test_rc06_offer_sorting_and_display_price`: Verified Offer 1 (in-stock, 149900) and Offer 2 (in-stock, 179900) sorted ahead of Offer 3 (out-of-stock, 129900).
- `test_rc06_display_price_all_out_of_stock`: Verified lowest out-of-stock offer price used when all offers are out of stock.
- `test_rc06_display_price_no_offers`: Verified fallback to canonical garment display price.
