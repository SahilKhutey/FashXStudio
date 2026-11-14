# Virtual Try-On (VTO) Provider Telemetry Specification

## 1. Overview

FashXStudio integrates upstream third-party AI image generation providers (primarily FASHN API) to synthesize virtual try-on renders.

Because third-party AI APIs are subject to variable queueing, external rate limits, upstream outages, and per-render billing, comprehensive operational telemetry is embedded directly inside `backend/fashx/infrastructure/tryon/fashn_api.py`.

## 2. Emitted VTO Metrics (`FashX/VTO`)

All external provider interactions emit CloudWatch EMF records:

| Metric Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `VTOJobSubmitted` | Counter | Count | A try-on inference job was successfully dispatched to the provider. |
| `VTOJobSucceeded` | Counter | Count | A try-on inference job completed successfully and generated a valid render. |
| `VTOJobFailed` | Counter | Count | A try-on inference job failed, was canceled, or errored upstream. |
| `VTOProviderLatency` | Timer | Milliseconds | Round-trip duration of HTTP calls to provider endpoints. |
| `VTOProviderTimeout` | Counter | Count | Polling loop exceeded maximum timeout (90 seconds). |
| `VTOProviderRateLimit` | Counter | Count | Provider returned HTTP 429 (Too Many Requests). |
| `VTOProviderAuthFailure` | Counter | Count | Provider returned HTTP 401 or 403 (Invalid API key or balance exhausted). |
| `VTOResultValidationFailure`| Counter | Count | Provider returned 200 OK but payload was corrupt or missing output URLs. |
| `VTOProviderCostEstimate` | Counter | None | Estimated USD cost increment per completed render. |

## 3. Allowed Dimensions & Cardinality Guardrails

To prevent high-cardinality custom metric proliferation:

### Allowed Dimensions
- `Environment`: `dev`, `staging`, `prod`
- `Stage`: Operational phase (`submit`, `poll_status`, `download_result`, `validate`)
- `Category`: Try-on garment category (`tops`, `bottoms`, `one-pieces`)

### Prohibited Dimensions
Provider job IDs (e.g. `fashn-job-948194`), model image URLs, user IDs, and auth headers must never be added as dimensions.

## 4. Cost and Quota Tracking

Each completed render increments `VTOProviderCostEstimate` by the contracted per-inference rate (e.g. `$0.075 USD`).
- Emitting this metric enables real-time CloudWatch metric math tracking and alerting on daily / weekly spend runaway.
- Correlating this metric with `ApiRequestsCount` ensures that retry loops or bot traffic do not cause unbounded financial exposure.

## 5. Failure Classification & CloudWatch Alarms

| Alarm Name | Metric & Threshold | Severity | Immediate Action |
| :--- | :--- | :--- | :--- |
| `VTO-Provider-Rate-Limit-Production` | `VTOProviderRateLimit > 3` in 5m | P2 | Scale down worker concurrency or contact vendor for rate limit tier increase. |
| `VTO-Provider-Auth-Failure-Production` | `VTOProviderAuthFailure > 0` in 1m | P1 | Immediate credential rotation or account billing refill. |
| `VTO-Failure-Rate-High-Production` | `VTOJobFailed > 5` in 5m | P1 | Check vendor status page, network routes, or payload schema changes. |
| `VTO-Provider-Timeout-Production` | `VTOProviderTimeout > 3` in 10m | P2 | Investigate vendor queue congestion; consider increasing timeout limit. |

## 6. Verification & Automated Testing

Telemetry behaviors are verified in `tests/observability/test_tryon_metrics.py`:
- `test_vto_submit_and_complete_metrics`: Asserts `VTOJobSubmitted`, `VTOJobSucceeded`, and `VTOProviderLatency`.
- `test_vto_rate_limit_metrics`: Simulates HTTP 429 response and confirms `VTOProviderRateLimit=1`.
- `test_vto_auth_failure_metrics`: Simulates HTTP 401 response and confirms `VTOProviderAuthFailure=1`.
- `test_vto_timeout_metrics`: Verifies `VTOProviderTimeout=1` when status polling exceeds time limit.
