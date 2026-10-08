# Dependency Register: Amazon Product Advertising API (PA-API v5)

| Attribute | Specification |
| :--- | :--- |
| **Provider** | Amazon Associates / Amazon Web Services |
| **Purpose** | Product search, pricing, availability, and affiliate link generation |
| **API Version** | PA-API v5.0 |
| **Account Status** | Associates account active; API credentials assigned |
| **Commercial Terms** | Standard Amazon Associates Operating Agreement |
| **License** | Proprietary Commercial API |
| **Commercial Permission** | Yes (Affiliate monetization permitted) |
| **Rate Limits** | 1 request per second initial quota (scales dynamically with driven sales) |
| **Owner** | Commerce & Catalog Subsystem Lead |

---

## 1. Integration Rules & Constraints

1. **Direct Scraping Prohibited**: Ingestion must use official PA-API v5 endpoints (`GetItems`, `SearchItems`).
2. **Price Stashing Limits**: Per Amazon Associates Operating Agreement, prices and availability cached locally must be refreshed at least once every 24 hours.
3. **Affiliate Link Tagging**: Outbound URLs must append the approved associate tracking tag (`AssociateTag`) and unique click sub-ID for conversion attribution.

---

## 2. Fallback & Circuit Breakers

If Amazon PA-API returns HTTP 429 (Too Many Requests) or undergoes service degradation:
- Circuit breaker opens after 5 consecutive failures.
- Feed falls back to secondary merchant offers (e.g. Myntra / Direct D2C) or cached catalog items with explicit *"Price verified as of [Time]"* disclaimer.
