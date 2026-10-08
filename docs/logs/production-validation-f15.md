# F15 — Production QA & Validation Gate

F15 validates the executable repository baseline. It is not a claim that external
commerce, map, weather, notification, payment, or fulfilment providers are live.

| Gate | Current evidence | Release condition |
| --- | --- | --- |
| Unit tests | `python -m pytest tests -p no:cacheprovider -q` | Pass on the release commit |
| Feature boundaries | F00–F14 modules and contracts | No direct provider/database bypass from feature domain code |
| Schema migration | `0013_onboarding_profiles.py` | Applied in the target database and smoke tested |
| API/client integration | Feature registry is routed | Add authenticated product/client workflow tests before public release |
| Security | No payment credentials or provider calls added | Threat model, authorization review, secret scan and dependency audit |
| Performance | Deterministic in-memory baselines | Load-test production adapters and APIs |
| Accessibility | State contracts documented | Test rendered screens with keyboard and assistive technology |
| External providers | Explicit adapter boundary only | Credentialed sandbox tests and operational runbooks |

## Required release evidence

1. Green test suite and migration dry run.
2. Environment-specific feature flags reviewed.
3. Authenticated API/mobile E2E tests for the chosen release slice.
4. Observability, backup/rollback, incident contact and privacy retention review.
5. Approval that each enabled external integration has passed sandbox verification.
