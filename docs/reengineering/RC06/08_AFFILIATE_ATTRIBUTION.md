# RC-06 — Affiliate Attribution & Link Tracking

## Tracking Query Parameters

To attribute user traffic and virtual try-on purchase conversions to partner merchant affiliate programs, FashX automatically appends standard attribution query parameters to outbound retailer links.

### Parameter Register

| Parameter | Standard Value | Description |
|---|---|---|
| `utm_source` | `fashx` | Traffic origin identifier |
| `utm_medium` | `app` | Channel identifier (mobile app) |
| `utm_campaign` | `vto_purchase` | Primary intent campaign |
| `sub_id` | `<user_id>` | User identifier for publisher reporting and commission reconciliation |
| `click_id` | `<buy_click_id>` | Unique click UUID generated per handoff event |

### Attribution Preservation
When appending tracking parameters, existing merchant query parameters on the original product link (such as SKU identifiers, category slugs, or partner tracking IDs) are preserved without overwriting:
```python
# Query parameters merging in CreateBuyClickUseCase
query_params = parse_qs(parsed.query)
query_params["utm_source"] = ["fashx"]
query_params["utm_medium"] = ["app"]
query_params["utm_campaign"] = ["vto_purchase"]
query_params["sub_id"] = [str(user_id)]
query_params["click_id"] = [str(click_event.id)]
new_query = urlencode(query_params, doseq=True)
```

### Conversion Confirmation Boundary
In accordance with FashX core commerce policies:
- An outbound click recorded by `/commerce/buy-clicks` is an attribution handoff, NOT confirmation of an order.
- The external retailer handles payment processing, fraud check, checkout, and shipping.
- FashX never simulates order confirmation or emits `purchase_confirmed` without verified affiliate network conversion postbacks.
