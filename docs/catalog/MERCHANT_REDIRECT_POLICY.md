# Merchant Redirect Policy

**Workstream**: 5.1.9 — Outbound Commercial Navigation & Redirection  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/authorization/`

---

## 1. Objective
When a shopper decides to purchase an item discovered on FashXStudio, they are redirected to the merchant's official digital storefront or checkout channel. This document defines the authorization requirements governing outbound commercial redirects.

---

## 2. Policy Invariant
> No outbound redirect to a merchant URL may be generated or served unless the originating `CatalogSource` holds an active, granted `MERCHANT_REDIRECT` permission.

---

## 3. Redirect Permission (`MERCHANT_REDIRECT`)

### 3.1 Allowed Navigation Patterns
- Direct deep-links to product detail pages (PDP) on the merchant's verified domain.
- Direct-to-cart or pre-filled checkout sessions where supported by merchant APIs.
- Universal Links / App Links opening the merchant's native mobile application.

### 3.2 Prohibited Behaviors
- Redirecting shoppers through unverified third-party ad networks or intermediary cloakers.
- Modifying target URLs to include unauthorized tracking scripts or parameters not consented to by the merchant.
- Redirecting to unauthorized domains outside the merchant's verified `website` host.

---

## 4. URL Validation & Security Standards
1. **Domain Whitelist**: Outbound URLs must match the domain or authorized subdomains of `merchants.website`.
2. **Protocol**: Must strictly use HTTPS with valid TLS certificates. HTTP redirects are rejected.
3. **UTM Attribution**: Standard attribution query parameters (`utm_source=fashx&utm_medium=discovery&utm_campaign=...`) are appended in conformance with contractual agreements.
