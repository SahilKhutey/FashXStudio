# RC07 — Hard Constraints & Gating Policy

## 1. Objective
Enforce strict eligibility filters prior to candidate scoring. A garment violating any hard constraint cannot be scored or surfaced in the discovery feed.

## 2. Mandatory Eligibility Gates
| Gate | Condition | Enforcement Point |
|---|---|---|
| Stock Status | `CanonicalGarment.in_stock == True` and `MerchantOffer.in_stock == True` | Database candidate query (`list_feed_candidates`) |
| Product Status | `CanonicalGarment.active == True` and `MerchantProduct.status == "active"` | Database candidate query (`list_feed_candidates`) |
| Source Clearance | `CatalogSource.status == "cleared"` and `rights_display == True` | Database candidate query (`list_feed_candidates`) |
| Budget Ceiling | `top_offer.price_minor <= UserPreference.budget_max` | `DeterministicFilter.filter_candidates` |
| Budget Floor | `top_offer.price_minor >= UserPreference.budget_min` | `DeterministicFilter.filter_candidates` |
| Color Exclusion | `garment.dominant_color not in UserPreference.colors_avoided` | `DeterministicFilter.filter_candidates` |
| Category Inclusion | `garment.category in UserPreference.categories` (if configured) | `DeterministicFilter.filter_candidates` |
| User Exclusions | `garment.id not in feed_exclusions` | `DeterministicFilter.filter_candidates` |
| Negative Signals | `garment.id not in {hide, not_interested, dislike}` | `DeterministicFilter.filter_candidates` |

## 3. Empty State Handling
When no candidates survive hard filtering:
- Returns HTTP 200 with `items: []`.
- `empty_reason`: `"catalog_empty"` if catalog has 0 candidates; `"all_candidates_filtered"` or `"no_matches_in_size_or_budget"` if constraints eliminated all candidates.

## 4. Verification
Integration tests `tests/integration/test_rc07_personalized_feed.py` and evaluation test `tests/evaluation/test_rc07_ranking_metrics.py` verify that constraint violation rate in the final feed is strictly **0.0%**.
