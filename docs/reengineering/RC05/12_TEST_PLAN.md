# RC05 — 12 Test Plan and Verification Matrix

## Objective
Provide an exhaustive test plan and verification matrix covering all 20 specified RC05 scenarios, unit suites, integration tests, contract tests, mobile Jest tests, and end-to-end smoke tests.

## Test Scenario Matrix
| Test ID | Scenario | Verification Method | Expected Result | Actual Result |
|---|---|---|---|---|
| **RC05-T01** | User has no active body-photo consent | Unit (`test_rc05_vto_scenarios.py`) | Rejection (`ConsentRequiredError`) | 🟢 Passed |
| **RC05-T02** | Photo belongs to another user | Unit (`test_rc05_vto_scenarios.py`) | Rejection (`ValidationError`) | 🟢 Passed |
| **RC05-T03** | Photo is not accepted | Unit (`test_rc05_vto_scenarios.py`) | Rejection (`ValidationError`) | 🟢 Passed |
| **RC05-T04** | Garment is not try-on eligible | Unit (`test_rc05_vto_scenarios.py`) | Rejection (`ApiError 422`) | 🟢 Passed |
| **RC05-T05** | Same idempotency key submitted twice | Unit & Smoke | Same job returned | 🟢 Passed |
| **RC05-T06** | Same inputs hit valid artifact cache | Unit (`test_rc05_vto_scenarios.py`) | Instant cache hit, no new inference | 🟢 Passed |
| **RC05-T07** | Provider returns authentication error | Unit (`test_tryon_adapters.py`) | Permanent failure (`provider_auth`) | 🟢 Passed |
| **RC05-T08** | Provider returns temporary outage | Unit (`test_tryon_adapters.py`) | Retryable failure (`provider_unavailable`) | 🟢 Passed |
| **RC05-T09** | Provider job ID already exists | Unit (`test_rc05_vto_scenarios.py`) | Resume collection without duplicate submit | 🟢 Passed |
| **RC05-T10** | Worker crashes after provider submission | Unit (`test_rc05_vto_scenarios.py`) | Collects result without re-submitting | 🟢 Passed |
| **RC05-T11** | Provider returns corrupt image | Unit (`test_tryon_adapters.py`) | Quality rejection | 🟢 Passed |
| **RC05-T12** | Signed URL expires | Router / Integration | Authorized refresh via status endpoint | 🟢 Passed |
| **RC05-T13** | User B requests User A's artifact | Unit & Smoke | HTTP 403 Forbidden | 🟢 Passed |
| **RC05-T14** | Consent revoked while job is queued | Unit (`test_rc05_vto_scenarios.py`) | Job cancelled (`consent_revoked`) | 🟢 Passed |
| **RC05-T15** | Consent revoked during processing | Unit (`test_rc05_vto_scenarios.py`) | No artifact delivered, job cancelled | 🟢 Passed |
| **RC05-T16** | Dispatcher failure observability | Unit & Smoke | Persisted job preserved, failure recorded | 🟢 Passed |
| **RC05-T17** | Mobile receives mock completed job | Mobile Jest (`tryon_screen.test.tsx`) | Preview-only warning displayed | 🟢 Passed |
| **RC05-T18** | Mobile receives failed job | Mobile Jest (`tryon_screen.test.tsx`) | Failure reason and retry action shown | 🟢 Passed |
| **RC05-T19** | Save completed look | Integration & Smoke | Wardrobe record created | 🟢 Passed |
| **RC05-T20** | User submits feedback | Integration & Smoke | Feedback persisted (HTTP 201) | 🟢 Passed |

## Execution Commands
```bash
# 1. Focused VTO Unit Suites
pytest tests/unit/test_rc05_provider_configuration.py \
       tests/unit/test_rc05_vto_scenarios.py \
       tests/unit/test_tryon_adapters.py \
       tests/unit/test_tryon_use_cases.py \
       tests/unit/test_tryon_cache_key.py \
       tests/unit/test_vto_job_orchestration.py \
       tests/unit/test_vto_provider_integration.py \
       tests/unit/test_vto_image_preparation.py \
       tests/unit/test_vto_phase6_artifacts.py \
       tests/unit/test_vto_phase9_feedback.py -q

# 2. Integration and Contract Suites
pytest tests/integration/test_tryon_orchestration.py \
       tests/contracts/test_tryon_adapter.py \
       tests/contracts/test_tryon_repo.py -q

# 3. Mobile Jest & Typecheck
npm --prefix mobile test -- --ci
npm --prefix mobile run typecheck

# 4. End-to-End VTO Smoke Harness
python scripts/rc05_vto_smoke.py
```

## Exit Criteria
- 100% of defined scenarios pass with genuine output evidence recorded.
