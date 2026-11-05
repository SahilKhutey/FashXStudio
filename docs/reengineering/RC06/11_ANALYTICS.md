# RC-06 — Commerce & Attribution Analytics

## Event Taxonomy & Instrumentation

To evaluate product conversion efficiency and measure merchant partner traffic, FashX records key telemetry events throughout the shopping funnel.

### 1. `buy_click` Event
- **Trigger:** Generated immediately upon successful creation of an outbound retailer handoff via `POST /commerce/buy-clicks`.
- **Properties:**
  - `buy_click_id`: UUID
  - `user_id`: UUID of caller
  - `garment_id`: UUID of canonical garment
  - `offer_id`: UUID of merchant offer
  - `merchant_id`: UUID of merchant
  - `price_minor`: Integer price at time of click
  - `currency`: ISO currency code (e.g., `"INR"`)
  - `created_at`: UTC timestamp

### 2. `wardrobe_item_saved` Event
- **Trigger:** Generated when a user saves a garment to their closet via `POST /wardrobe/items`.
- **Properties:**
  - `user_id`: UUID
  - `garment_id`: UUID
  - `offer_id`: UUID (optional)
  - `snapshot_price_minor`: Integer price
  - `created_at`: UTC timestamp

### 3. Observability & Privacy Protections
- Analytics events are persisted in the database using the shared session factory.
- Personally identifiable information (PII) such as user emails or exact IP addresses are never attached to outbound attribution parameters.
- Only pseudonymized `user_id` is passed as `sub_id` for affiliate publisher attribution.
