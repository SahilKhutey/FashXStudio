# Profile Validation Rules and Invariants

## 1. Physical Measurements Invariants
1. **Height Range**:
   - Must be between `80.0 cm` and `250.0 cm` inclusive if provided.
   - Values below 80.0 cm or above 250.0 cm are rejected with HTTP 422 Unprocessable Entity.
   - Field is completely optional (`None` is permitted).

2. **Weight Range**:
   - Must be between `20.0 kg` and `400.0 kg` inclusive if provided.
   - Values below 20.0 kg or above 400.0 kg are rejected with HTTP 422 Unprocessable Entity.
   - Field is completely optional (`None` is permitted).

3. **Strict Non-Medical Posture**:
   - System strictly treats height and weight as geometric sizing parameters for garment fit.
   - No body mass index (BMI) calculation, health classification, or medical diagnostic assessment is performed or stored.

## 2. Controlled Enums Validation
1. **Size Systems**:
   - Only `IN`, `US`, `UK`, `EU`, `INTL` are accepted. Unknown codes reject with 422.
2. **Preferred Fit**:
   - Only `SLIM`, `REGULAR`, `RELAXED`, `OVERSIZED`, `NO_PREFERENCE` are accepted.
3. **Style Preferences**:
   - Only valid `StylePreference` entries are accepted (`CASUAL`, `FORMAL`, `SMART_CASUAL`, `MINIMAL`, `STREETWEAR`, `SPORTSWEAR`, `ETHNIC`, `TRADITIONAL`, `FUSION`, `PARTY`, `NO_PREFERENCE`).
4. **Color Preferences**:
   - Only valid `ColorPreference` entries are accepted (`BLACK`, `WHITE`, `GREY`, `NAVY`, `BLUE`, `RED`, `GREEN`, `YELLOW`, `ORANGE`, `PINK`, `PURPLE`, `BROWN`, `BEIGE`, `MAROON`, `MULTICOLOR`, `NO_PREFERENCE`).

## 3. Shopping & Budget Invariants
1. **Budget Range Invariant**:
   - `budget.min` must be >= 0.
   - `budget.max` must be >= 0.
   - If both `budget.min` and `budget.max` are specified, `budget.min <= budget.max`. Payloads where `budget.min > budget.max` are rejected with HTTP 422.

## 4. Mass-Assignment & Extra Attributes
1. **Strict Field Whitelisting**:
   - `ShopperProfileCreate` and `ShopperProfileUpdate` enforce `model_config = ConfigDict(extra="forbid")`.
   - Any extra fields (such as `user_id`, `id`, `version`, `created_at`, `updated_at`, `is_admin`, etc.) trigger immediate 422 validation failure.
