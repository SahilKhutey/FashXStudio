# 01 — Fit Profile Architecture

## 1. End-to-End Architecture

```mermaid
flowchart TD
    Shopper[Authenticated Shopper] --> MobileUI[Mobile FitProfileScreen & MeasurementInput]
    MobileUI --> API[Authenticated Fit Profile API /api/v1/profile/fit]
    API --> PrincipalCheck[Principal Ownership Guard]
    PrincipalCheck --> ConsentSvc[FitConsentService]
    ConsentSvc --> FitService[FitProfileService]
    FitService --> Val[Unit Normalization & Range Validation]
    FitService --> Policy[Versioned Category Policy Engine]
    FitService --> Repo[(FitProfileRepository)]
    Repo --> ShopperProfiles[(shopper_profiles)]
    Repo --> Measurements[(profile_measurements)]
    Repo --> History[(profile_measurement_history)]
    Repo --> CatPrefs[(category_fit_preferences)]
    Repo --> Audit[(profile_audit_events)]
    FitService -->|On Update / Withdrawal / Delete| Invalidate[Invalidate FitRecommendation Cache]
```

## 2. Service Boundaries

- **Shopper Fit Profile (`fashx.profile`)**: Stores shopper body measurements (`BODY`), measurement history, subjective fit preferences, and purpose-specific consent. Never calculates garment recommendations directly.
- **Merchant Size Data (`fashx.catalog.size_charts`)**: Stores merchant garment size charts (`GARMENT` or merchant `BODY` tables). Kept strictly isolated from shopper records.
- **Virtual Try-On (`fashx.tryon`)**: Generates visual try-on images only. VTO outputs are explicitly rejected as measurement evidence by `FitProfileService.reject_vto_as_measurement_evidence`.
