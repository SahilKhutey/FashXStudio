# Source Registry Specification

**Workstream**: 5.1.3 — Catalog Source Registry  
**Status**: Active  
**Module**: `backend/fashx/catalog/sources/`

---

## 1. Overview
A single merchant may supply product data through multiple technical channels (e.g., a direct REST API for high-frequency pricing updates, a nightly CSV feed for bulk seasonal inventory, and a Shopify App integration for direct merchant stores). The `CatalogSource` entity models each technical ingestion channel independently under a parent `Merchant`.

---

## 2. Multi-Source Hierarchy

```
                      +-----------------------------+
                      |          Merchant           |
                      |   (Legal Entity & Status)   |
                      +-----------------------------+
                                     |
           +-------------------------+-------------------------+
           |                                                   |
           v                                                   v
+-------------------------+                         +-------------------------+
|     CatalogSource A     |                         |     CatalogSource B     |
| (REST API Integration)  |                         | (Nightly HTTPS Feed)    |
| - Status: ACTIVE        |                         | - Status: ACTIVE        |
| - OAuth2 Secret Ref     |                         | - SFTP / HTTPS Key Ref  |
+-------------------------+                         +-------------------------+
           |                                                   |
  +--------+--------+                                 +--------+--------+
  |                 |                                 |                 |
  v                 v                                 v                 v
Evidence        Permissions                        Evidence        Permissions
```

---

## 3. Source Data Contract

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | UUID | Yes | Primary key |
| `merchant_id` | UUID | Yes | Foreign key to parent `merchants.id` |
| `slug` | String | Yes | Unique human-readable identifier (e.g. `zara-in-api`) |
| `source_name` | String(160) | Yes | Display name for operational dashboards |
| `source_type` | Enum | Yes | `MERCHANT_API`, `AFFILIATE_API`, `MERCHANT_FEED`, `PARTNER_EXPORT`, `SHOPIFY_APP`, `OTHER_AUTHORIZED` |
| `access_method` | Enum | Yes | `OAUTH2`, `API_KEY`, `SIGNED_REQUEST`, `WEBHOOK`, `SFTP`, `HTTPS_FEED`, `MANUAL_PARTNER_EXPORT` |
| `credential_secret_ref` | String(512) | No | AWS Secrets Manager ARN or path; never stores raw keys |
| `source_status` | Enum | Yes | `PENDING_REVIEW`, `APPROVED`, `ACTIVE`, `SUSPENDED`, `EXPIRED`, `REVOKED`, `REJECTED` |
| `market_codes` | JSON List | Yes | ISO country codes this source is authorized for (e.g. `["IN"]`) |
| `category_codes` | JSON List | Yes | Authorized garment categories (e.g. `["apparel", "accessories"]`) |
| `refresh_hours` | Integer | Yes | Frequency of catalog refresh (default 24h) |
| `max_rps` | Float | Yes | Maximum permitted requests per second |
| `effective_at` | DateTime | No | Date source authorization becomes active |
| `expires_at` | DateTime | No | Hard expiration date of source contract |
| `next_review_at` | DateTime | No | Scheduled compliance review date |

---

## 4. Multi-Source Isolation Invariant
- **Independent Suspension**: A takedown or security notice affecting `CatalogSource A` suspends only `CatalogSource A`. `CatalogSource B` under the same merchant remains active unless the parent merchant is suspended.
- **Cascade Suspension**: When a parent `Merchant` is suspended, all child `CatalogSource` entities are immediately transitioned to `SUSPENDED`.
- **Per-Source Rights & Evidence**: Permissions and evidence are granted per source. Granting rights on one source does not imply rights on another source.
