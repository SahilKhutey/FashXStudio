# Fit Recommendation Policy

> **Rules governing evidence requirements, fail-closed states, and model evaluation.**

## 1. Evidence Requirements
A fit recommendation requires three independent, validated pillars:
1. **Consented Shopper Measurements**: Explicitly provided by the shopper or collected via a validated measurement process with active consent. Must include dimensional attributes (chest, waist, etc.). Height and weight alone are insufficient.
2. **Verified Merchant Size Chart**: Current (non-stale), verified source, explicit basis (`BODY` vs `GARMENT`), and known unit.
3. **Validated Fit Model**: Category-specific rule or statistical engine calibrated for that apparel category.

## 2. Deterministic Outcomes
- **`RECOMMENDED`**: A single definitive size recommendation supported by evidence.
- **`POSSIBLE_ALTERNATIVES`**: Multiple sizes fall within acceptable ease tolerance.
- **`INSUFFICIENT_DATA`**: Missing measurements, missing chart, or unverified source.
- **`STALE_SIZE_CHART`**: Merchant size chart was last verified $>90$ days ago.
- **`UNSUPPORTED_CATEGORY`**: No calibrated model exists for this garment type.
- **`CONFLICTING_DATA`**: Conflicting proportions (e.g. chest implies XL while waist implies XS).
- **`NO_AVAILABLE_SIZE`**: Shopper measurements fall outside all available merchant sizes.

## 3. Invalidation Policy
Fit recommendations must be immediately invalidated when:
- Shopper updates their body measurements or withdraws consent.
- Merchant updates or withdraws their product size chart.
- Product is delisted or in-stock sizes change.
- Fit model configuration version is bumped.
