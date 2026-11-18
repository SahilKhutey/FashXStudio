# Source Health Monitoring & Telemetry

## 1. Health States

The health of a catalog source is tracked using `SourceHealthState` (`backend/fashx/catalog/acquisition/contracts_v2.py`):

| State | Condition |
| :--- | :--- |
| `UNKNOWN` | Newly registered source with no recorded sync runs. |
| `HEALTHY` | Recent sync runs completed successfully within the expected refresh schedule. |
| `DEGRADED` | 1 or more recent sync runs failed due to transient network or server errors. |
| `RATE_LIMITED` | Latest run failed with HTTP 429 Too Many Requests. Throttled. |
| `AUTH_FAILED` | Latest run failed with authentication or permission errors (401/403). |
| `STALE` | No successful sync run completed within 2x the source's configured `refresh_hours`. |
| `DISABLED` | Source status is `SUSPENDED`, `REVOKED`, or `REJECTED`. |

## 2. Telemetry and Diagnostics (`SourceHealthChecker`)

`SourceHealthChecker` (`backend/fashx/catalog/acquisition/health.py`) computes real-time health reports by inspecting:
- `CatalogSource.source_status`
- The latest 5 `CatalogSyncRun` records for failure ratios and error codes
- `CatalogSource.last_successful_sync_at` against `refresh_hours`

### Lightweight Probe
The `perform_probe(session, source_id, adapter)` method provides non-disruptive connectivity checks:
- Triggers adapter `health_check()` (e.g. lightweight HEAD or 1-item test request).
- Measures roundtrip latency in milliseconds.
- Updates `last_authorization_check_at` on the `CatalogSource` record.

## 3. Administrative REST Endpoints

1. `GET /api/v1/admin/catalog/sources/{source_id}/health`: Evaluates current health state.
2. `POST /api/v1/admin/catalog/sources/{source_id}/health-check`: Executes a live diagnostic probe.
3. `GET /api/v1/admin/catalog/sources/{source_id}/sync-runs`: Returns historical execution metrics.
4. `GET /api/v1/admin/catalog/sync-runs/{run_id}`: Fetches granular page and product statistics for a specific run.
5. `GET /api/v1/admin/catalog/sources/{source_id}/checkpoints`: Returns current cursors and watermarks.
