# Search Subsystem Test Plan (SRCH-001 through SRCH-040)

## 1. Test Matrix Overview
Validates 40 distinct acceptance criteria across keyword matching, category & brand filtering, price/currency rules, size variant availability, occasion/color/fabric matching, semantic retrieval, visual similarity, RRF hybrid ranking, cursor pagination, no-result handling, freshness, and takedown enforcement.

---

## 2. Test Specifications (SRCH-001 through SRCH-040)

| Test ID | Area | Description | Verification Method |
| :--- | :--- | :--- | :--- |
| **SRCH-001** | Keyword | Exact keyword match returns relevant product | Full-text query test |
| **SRCH-002** | Keyword | Partial keyword matches product title | Partial token match |
| **SRCH-003** | Keyword | Case variation yields identical results | Case-insensitive test |
| **SRCH-004** | Keyword | Empty query defaults to browse or valid error | Query validation test |
| **SRCH-005** | Keyword | Excessively long query (>200 chars) rejected | Length validation test |
| **SRCH-006** | Category | Category filter matches leaf taxonomy ID | Category filter test |
| **SRCH-007** | Category | Parent category includes descendant items | Category hierarchy test |
| **SRCH-008** | Brand | Brand filter restricts to canonical brand | Brand filter test |
| **SRCH-009** | Brand | Brand alias maps to canonical brand | Alias resolution test |
| **SRCH-010** | Price | Price range filters active eligible offer | Offer price filter test |
| **SRCH-011** | Price | Invalid price range (min > max or negative) rejected | Price validation test |
| **SRCH-012** | Price | Currency mismatch prevents invalid comparisons | Currency validation test |
| **SRCH-013** | Color | Color filter matches normalized taxonomy color | Color filter test |
| **SRCH-014** | Color | Multi-color product matches any selected color | Multi-color test |
| **SRCH-015** | Size | Size filter matches supported variant SKU in stock | Sizing stock test |
| **SRCH-016** | Size | Unknown size never falsely treated as in stock | Unknown size reject test |
| **SRCH-017** | Size | Out-of-stock size excluded when in_stock=true | Out-of-stock exclusion |
| **SRCH-018** | Occasion | Occasion filter matches approved attributes | Occasion filter test |
| **SRCH-019** | Semantic | Semantic query returns conceptually related items | Vector cosine test |
| **SRCH-020** | Semantic | Incompatible embedding dimension rejected | Invariant check |
| **SRCH-021** | Visual | Reference image returns visually similar items | Nearest-neighbor test |
| **SRCH-022** | Visual | Unauthorized reference image rejected | Permission check test |
| **SRCH-023** | Ranking | Title & brand matches rank above description | Ranking boost test |
| **SRCH-024** | Sorting | Price low-to-high and high-to-low sorting | Sort ordering test |
| **SRCH-025** | Pagination | Cursor pagination yields zero duplicate items | Pagination stability test |
| **SRCH-026** | Pagination | Malformed or expired cursor token rejected | Cursor validation test |
| **SRCH-027** | No-Results | Zero-result response returns useful suggestions | Suggestion engine test |
| **SRCH-028** | Freshness | Delisted or inactive product excluded from search | Product status test |
| **SRCH-029** | Freshness | Takedown product immediately excluded | Hard takedown test |
| **SRCH-030** | Freshness | Stale price / offer excluded by policy | Stale threshold test |
| **SRCH-031** | Security | Cross-tenant merchant data excluded | Tenant isolation test |
| **SRCH-032** | Hybrid | RRF correctly fuses keyword & vector candidates | RRF merger test |
| **SRCH-033** | Documents | Updated catalog data refreshes search document | Document update test |
| **SRCH-034** | Cache | Invalidate cache removes taken-down product | Cache purge test |
| **SRCH-035** | Facets | Facet counts reflect eligible filtered results | Facet calculation test |
| **SRCH-036** | Analytics | Search events recorded in product_search_events | Event recording test |
| **SRCH-037** | Combinations | Complex AND/OR filter combinations behave properly | Composite filter test |
| **SRCH-038** | Multi-Offer | Different merchants selling same garment segregated | Listing unit test |
| **SRCH-039** | Confidence | Low-confidence attributes not treated as facts | Policy gate test |
| **SRCH-040** | Security | SQL injection in search text safely neutralized | Injection safety test |
