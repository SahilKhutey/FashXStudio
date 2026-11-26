# Phase 08.2 — Shopper Fit Profile

## Objective

Build a secure, shopper-controlled profile containing manually entered body measurements and subjective fit preferences. This profile provides structured evidence for future category-specific fit-intelligence features.

## Scope

- Required and optional measurement definitions.
- Category-specific measurement requirements (`fit_policy.py`).
- Shopper-facing measurement explanations (`measurement_definitions.py`).
- Manual measurement entry workflow.
- Unit validation and deterministic normalization (`units.py`).
- Measurement range validation (`validation.py`).
- Measurement provenance, status states, and per-measurement timestamps.
- Measurement updates with optimistic locking and immutable history (`profile_measurement_history`).
- Default fit preference and independent category-specific preferences (`category_fit_preferences`).
- Brand-size independence policy (cross-brand label conversion prohibited).
- Authenticated profile APIs (`/api/v1/profile/fit`).
- Mobile profile components, Zustand store, and API integration (`mobile/src/features/fit-profile/`).
- Purpose-specific consent, access control, zero-PII logging, retention, and deletion integration.

## Architectural Rules

1. Product browsing does not require body measurements.
2. Required measurements depend on the supported garment category and versioned fit policy.
3. Optional measurements must not block profile creation.
4. Body measurements (`measurement_subject = BODY`) and merchant garment measurements are stored separately.
5. Original measurement values and units must be preserved alongside normalized canonical values (`CM` / `KG`).
6. Measurement timestamps distinguish measured time (`measured_at`) from storage (`created_at`) and update (`updated_at`) time.
7. Measurement updates enforce optimistic concurrency (`expected_version`) and preserve history.
8. Fit preferences are subjective comfort signals and are not physical-fit evidence.
9. Category preferences are stored independently and resolved deterministically.
10. One brand's size label is never assumed equivalent to another brand's size label.
11. Virtual try-on outputs must never be used as measurement evidence.
12. Profile access is authenticated and strictly shopper-owned.
13. Consent withdrawal halts future processing for the withdrawn purpose.

## Documentation Package

| Document | File |
|---|---|
| Architecture | [01-fit-profile-architecture.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/01-fit-profile-architecture.md) |
| Measurement Requirements | [02-measurement-requirements.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/02-measurement-requirements.md) |
| Measurement Guidance | [03-measurement-guidance.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/03-measurement-guidance.md) |
| Manual Measurement Entry | [04-manual-measurement-entry.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/04-manual-measurement-entry.md) |
| Unit Normalization | [05-unit-normalization.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/05-unit-normalization.md) |
| Measurement Validation | [06-measurement-validation.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/06-measurement-validation.md) |
| Timestamps & History | [07-timestamps-and-history.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/07-timestamps-and-history.md) |
| Fit Preferences | [08-fit-preferences.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/08-fit-preferences.md) |
| Category Preferences | [09-category-preferences.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/09-category-preferences.md) |
| Brand Size Independence | [10-brand-size-independence.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/10-brand-size-independence.md) |
| Profile API | [11-profile-api.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/11-profile-api.md) |
| Mobile UI | [12-mobile-ui.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/12-mobile-ui.md) |
| Consent, Security & Privacy | [13-consent-security-and-privacy.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/13-consent-security-and-privacy.md) |
| Database Migrations | [14-database-migrations.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/14-database-migrations.md) |
| Test Plan | [15-test-plan.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/15-test-plan.md) |
| Execution Report | [16-execution-report.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/16-execution-report.md) |
| Release Checklist | [17-release-checklist.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.2-shopper-fit-profile/17-release-checklist.md) |
