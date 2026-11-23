# Product Validation Rules

## 1. Overview

Before normalization or persistence, every raw product record undergoes validation via `validate_product_record()`. Records failing validation are redirected to quarantine and never published to the consumer catalog.

---

## 2. Rule Definitions & Reason Codes

| Field | Rule Code | Condition for Rejection | Quarantine Action |
| :--- | :--- | :--- | :--- |
| `source_product_id` | `missing_product_id` | Field is empty, whitespace only, or `None`. | Quarantine; status `PENDING` |
| `source_product_id` | `invalid_product_id` | Exceeds 255 chars, or contains control characters. | Quarantine; status `PENDING` |
| `title` | `invalid_title` | Title is empty, whitespace only, or exceeds 500 chars. | Quarantine; status `PENDING` |
| `currency` | `missing_currency` | Currency is empty or not provided. | Quarantine; status `PENDING` |
| `currency` | `unsupported_currency` | Currency code not in ISO 4217 supported list (`INR`, `USD`, `EUR`, `GBP`, `JPY`). | Quarantine; status `PENDING` |
| `price_minor` | `invalid_price` | Price is missing, non-numeric, or `<= 0`. | Quarantine; status `PENDING` |
| `category` | `category_unmapped` | Category cannot be mapped to the canonical taxonomy. | Quarantine; status `PENDING` |
| `product_url` | `invalid_product_url` | Scheme is not HTTPS, host is invalid, or URL contains embedded credentials (`user:pass@`). | Quarantine; status `PENDING` |
| `product_url` | `disallowed_domain` | URL host does not match merchant's authorized domain list (if configured). | Quarantine; status `PENDING` |

---

## 3. URL Hardening Rules

1. **Protocol Requirement**: All outbound URLs must strictly use `https://`. Insecure `http://` links are rejected.
2. **Credential Stripping**: Any URL containing user credentials in the authority component (e.g., `https://user:pass@domain.com/`) is quarantined immediately.
3. **Domain Whitelisting**: If a source configures an `allowed_domains` restriction in `metadata_json`, any outbound link targeting a different domain is rejected.
