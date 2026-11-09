# RC11: Automated Test Plan & Matrix

## 1. Test Architecture
The RC11 test plan covers pilot metric mathematics, data validation, privacy quarantine, analytics contracts, and prerequisite authorization gating:

```
tests/
├── unit/
│   └── test_rc11_pilot_metrics.py
├── integration/
│   └── test_rc11_analytics_contract.py
└── release/
    └── test_rc11_pilot_authorization.py
```

## 2. Test Matrix

| Test Module | Coverage | Invariant Validated |
| :--- | :--- | :--- |
| [`test_rc11_pilot_metrics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/unit/test_rc11_pilot_metrics.py) | Unit | `ratio()`, `percentile()`, nearest rank math, missing field detection, simulated evidence rejection, full fixture pass, stop rule triggers (exposure, crashes). |
| [`test_rc11_analytics_contract.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/integration/test_rc11_analytics_contract.py) | Integration | `ProductJourneyEvent` schema v1 contract, PII regex detection (email, phone, signed URLs), forbidden measurement keys. |
| [`test_rc11_pilot_authorization.py`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/release/test_rc11_pilot_authorization.py) | Release | Fail-closed authorization engine: blocks pilot without G1–G5 and RC08/RC10 prerequisites. |

## 3. Execution Commands
```bash
# RC11 Test Suites
pytest tests/unit/test_rc11_pilot_metrics.py \
       tests/integration/test_rc11_analytics_contract.py \
       tests/release/test_rc11_pilot_authorization.py -q

# Full Repository Regression
pytest tests/unit/test_rc10_*.py tests/release/test_rc10_beta_gates.py -q

# Mobile Integrity Suite
cd mobile && npx tsc --noEmit && npx eslint . --max-warnings 0 && npx jest --ci
```
