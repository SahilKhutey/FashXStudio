# RC05 — 02 Provider Configuration

## Objective
Establish a fail-closed, commercially gated provider selection mechanism. Ensure unauthorized providers or missing credentials fail immediately rather than silently falling back to mock execution.

## Existing State
- `backend/fashx/core/dependencies.py` allowed arbitrary unknown strings in `TRYON_PROVIDER` to fall through to `MockAdapter()`.
- Mock adapter was usable without explicit selection in development environments.

## Changes
- Modified `backend/fashx/core/dependencies.py`:
  - Explicit match for `s.tryon_provider == "mock"`.
  - Raised explicit `ValueError(f"Unknown or unsupported tryon_provider: {s.tryon_provider}")` on unmapped provider strings.
  - Preserved `NotImplementedError` on `fashn_selfhost`.
  - Preserved `assert_production_license(adapter)` guard when `ENV=prod`.
  - Preserved `ValueError("FASHN_API_KEY required when TRYON_PROVIDER=fashn_api")`.
- Added automated test suite `tests/unit/test_rc05_provider_configuration.py`.

## Contracts
| Environment (`ENV`) | Provider (`TRYON_PROVIDER`) | Behavior |
|---|---|---|
| `dev` / `test` | `mock` | Composited image with `"PREVIEW ONLY"` watermark |
| `dev` / `test` | `fashn_api` | Hosted FASHN inference (requires `FASHN_API_KEY`) |
| `prod` | `fashn_api` | Commercially cleared inference |
| `prod` | `mock` | Rejected (`RuntimeError: Mock not allowed in production`) |
| Any | `fashn_selfhost` | Rejected (`NotImplementedError`) |
| Any | *unknown* | Rejected (`ValueError`) |

## Implementation
```python
# backend/fashx/core/dependencies.py
if s.tryon_provider == "fashn_api":
    if not s.fashn_api_key or not s.fashn_api_key.get_secret_value():
        raise ValueError("FASHN_API_KEY required when TRYON_PROVIDER=fashn_api")
    ...
elif s.tryon_provider == "fashn_selfhost":
    raise NotImplementedError(
        "fashn_selfhost try-on adapter is not implemented; mock fallback is forbidden"
    )
elif s.tryon_provider == "mock":
    adapter = MockAdapter()
else:
    raise ValueError(f"Unknown or unsupported tryon_provider: {s.tryon_provider}")
```

## Execution
```bash
pytest tests/unit/test_rc05_provider_configuration.py -v
```

## Tests
- `test_mock_provider_is_explicit_in_development` -> PASSED
- `test_unknown_provider_does_not_silently_fallback` -> PASSED
- `test_self_hosted_provider_is_not_silently_mocked` -> PASSED
- `test_mock_adapter_rejected_in_production` -> PASSED
- `test_fashn_api_key_required_for_fashn_provider` -> PASSED

## Risks
- Production deployment configured without provider keys.
- Mitigation: Container startup and dependency injection fail-fast before serving traffic.

## Evidence
```
tests/unit/test_rc05_provider_configuration.py: 5 passed in 2.03s
```

## Exit Criteria
- Provider configuration is strictly validated and fail-closed.
