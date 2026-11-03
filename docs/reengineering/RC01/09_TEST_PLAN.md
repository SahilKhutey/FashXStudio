# RC-01 — Test Plan & Verification Matrix

## Testing Strategy
1. **Unit Testing**: Validate recommendation logic, cold-start handling, and empty-state diagnostics without reliance on production embedding services.
2. **Integration Testing**: Validate database interactions across catalog, wardrobe, and profile use cases.
3. **Security & Route Snapshot Testing**: Verify that API routes adhere to the frozen route snapshot policy under `-m "not frozen"`.

## Executed Test Suites & Results

| Test Suite | File Path | Focus | Result |
| :--- | :--- | :--- | :--- |
| **Recommendation Unit Tests** | `tests/unit/test_recommendation_use_case.py` | `GenerateFeedUseCase` cold-start in `prod`, empty feed reporting, candidate filtering | 🟢 3 passed in 1.89s |
| **Discovery Personalization** | `tests/unit/test_mvp3_discovery_personalization.py` | Feed candidate scoring, personalized ranking, filter gates | 🟢 4 passed in 1.93s |
| **Wardrobe Journey** | `tests/unit/test_mvp5_closet_shopping_journey.py` | Wardrobe save, list, delete, and duplicate handling | 🟢 10 passed in 2.68s |
| **Core Settings** | `tests/unit/test_settings.py` | Settings parsing, database URI resolution, security secrets | 🟢 1 passed in 0.54s |
| **Security Suite** | `tests/security/` (with `-m "not frozen"`) | Route snapshot validation, token validation, scope enforcement | 🟢 82 passed in 39.52s |
| **RC-00 Audit Framework** | `audit/rc00/tests/` | Baseline inventory, mobile audit, runtime audit scripts | 🟢 6 passed in 0.06s |

## Test Execution Command Reference
```powershell
# Run recommendation tests
.venv\Scripts\pytest tests/unit/test_recommendation_use_case.py -v

# Run security suite (excluding ADR-0001 frozen commerce routes)
.venv\Scripts\pytest tests/security -m "not frozen" -v

# Run closet shopping journey tests
.venv\Scripts\pytest tests/unit/test_mvp5_closet_shopping_journey.py -v
```
