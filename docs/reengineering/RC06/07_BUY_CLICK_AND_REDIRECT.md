# RC-06 — Buy-Click Attribution & Safe Outbound Redirect

## Endpoint: `POST /commerce/buy-clicks`

The primary commerce handoff endpoint records outbound affiliate purchase intents, attaches attribution parameters, and validates the retailer destination URL before returning the redirect URL to the client.

### Request Body (`BuyClickRequest`)
```json
{
  "garment_id": "c1f73719-74d1-4e78-9e6a-29759c381c81",
  "offer_id": "e6a17b08-360b-4682-959c-6b3a36db8a1f"
}
```

### Response Body (`BuyClickResponse`)
```json
{
  "buy_click_id": "d8b39201-9a7c-48be-a6b1-0482591fa308",
  "redirect_url": "https://www.myntra.com/shirts/harbour-bay-navy-linen?utm_source=fashx&utm_medium=app&utm_campaign=vto_purchase&sub_id=4c281d77-6a45-420a-8d19-8c5da84fe18e&click_id=d8b39201-9a7c-48be-a6b1-0482591fa308",
  "tracking_id": "fashx_track_d8b39201"
}
```

## Security & Business Invariants

### 1. Mandatory `offer_id`
Previously, `offer_id` was optional and fell back silently to `offers[0].id`. Under RC-06:
- `offer_id: UUID` is strictly required.
- Requests lacking `offer_id` are rejected with `422 Unprocessable Entity`.
- No implicit fallback offer selection is permitted.

### 2. Caller Identity Binding
- The user ID is derived strictly from the JWT token principal (`UUID(principal.user_id)`).
- If the client sends a `user_id` in the JSON request body that does not match `principal.user_id`, the endpoint immediately raises `403 Forbidden`:
  ```python
  if req.user_id is not None and req.user_id != effective_user_id:
      raise ApiError(status_code=status.HTTP_403_FORBIDDEN, message="Cannot record buy clicks for another user")
  ```

### 3. Out of Stock Offer Rejection
- If the selected offer has `in_stock is False`, the buy-click request is rejected with `409 Conflict`:
  ```python
  if not offer.in_stock:
      raise ValidationError("Offer is out of stock")
  ```

### 4. Retailer URL Validation (`validate_retailer_url`)
Every retailer URL is validated against strict security rules before attribution parameters are appended:
- **Protocol:** Must strictly be `https://` (rejects `http://`, `javascript:`, `ftp://`, `data:`, etc.).
- **No Credentials:** Rejects URLs containing `user:pass@host`.
- **Valid Hostname:** Rejects empty hostnames, whitespace in hostnames, and malformed structures.
- **Allowed Hosts:** In production, `FASHX_RETAILER_ALLOWED_HOSTS` is mandatory. The destination hostname must exactly match an approved host or be a subdomain ending with `.<approved_host>`.
- **Fail Closed:** If `is_production` is True and no allowed hosts are configured, the service fails fast on startup.
