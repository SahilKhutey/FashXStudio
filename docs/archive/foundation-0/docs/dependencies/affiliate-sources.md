# Dependency Register: Multi-Merchant Affiliate Networks & D2C Connectors

| Attribute | Specification |
| :--- | :--- |
| **Networks** | Cuelinks, vCommission, Myntra Direct Affiliate, Brand Shopify Storefront APIs |
| **Purpose** | Outbound monetization, deep-link redirect tracking, commission attribution |
| **Account Status** | Aggregator networks registered |
| **Commercial Terms** | Cost-Per-Acquisition (CPA) / Cost-Per-Sale (CPS) |
| **License** | Commercial Network Terms |
| **Owner** | Commerce Subsystem Lead |

---

## 1. Multi-Merchant Attribution Architecture

```
User "Buy" Click
       │
       ▼
POST /api/v1/commerce/buy-click
       │
       ▼
Commerce Service attaches internal `click_id` & `affiliate_sub_id`
       │
       ▼
Redirects user to merchant checkout
       │
       ▼
Postback Webhook received from affiliate network
       │
       ▼
Attribution Event recorded: matches `click_id` -> calculates net commission
```

---

## 2. Direct D2C / Shopify Integration Policy

As mandated in the architectural corrections:
- Direct D2C brands are integrated via **merchant-specific Storefront API agreements**, not unauthenticated web scraping or generic marketplace access.
- Each merchant requires its own API credentials and rate limit allocations.
