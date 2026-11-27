# 06 — Missing Data & Abstention Policy

Missing, stale, unauthorized, or conflicting inputs are modeled as explicit first-class outcomes rather than errors or guessed defaults.

| Condition | Missing Code | Outcome Status |
|---|---|---|
| Required shopper measurement missing | `SHOPPER_MEASUREMENT_MISSING` + field names | `INSUFFICIENT_INFORMATION` |
| Merchant chart missing or empty | `SIZE_CHART_MISSING` | `INSUFFICIENT_INFORMATION` |
| Basis is `UNKNOWN` | `MEASUREMENT_BASIS_UNKNOWN` | `INSUFFICIENT_INFORMATION` |
| Chart exceeds 90-day freshness window | `CHART_STALE` | `STALE_DATA` |
| Shopper measurement exceeds 180-day freshness | `SHOPPER_MEASUREMENT_STALE` | `STALE_DATA` |
| Chart conflict / merchant mismatch / extreme proportion ratio | `CHART_CONFLICT` | `CONFLICTING_DATA` |
| Category disabled or unvalidated | `CATEGORY_UNSUPPORTED` | `UNSUPPORTED_CATEGORY` |
| Zero available matching variants | `VARIANT_UNAVAILABLE` | `NO_AVAILABLE_SIZE` |
| Required `EaseRule` absent for `GARMENT` chart | `FIT_POLICY_MISSING` | `INSUFFICIENT_INFORMATION` |
| Consent withdrawn / source suspended / takedown | `PERMISSION_INVALID` | `INSUFFICIENT_INFORMATION` |
