# Staging Post-Deployment Smoke Tests

## 1. Overview

Smoke testing provides immediate, automated verification of the deployed staging API. Smoke tests evaluate whether the service is alive, ready, correctly configured, and serving traffic through the Application Load Balancer (ALB).

Smoke tests run automatically in GitHub Actions via `scripts/staging/validate_deployment.py` and `scripts/release/smoke.py`.

## 2. Tested Endpoints & Expected Behaviors

| Endpoint | Method | Required Auth | Purpose | Success Criteria |
| :--- | :--- | :--- | :--- | :--- |
| `/healthz/live` | GET | None | Container liveness probe | HTTP 200 `{"status": "ok"}` |
| `/healthz/ready` | GET | None | Dependency readiness probe | HTTP 200 `{"status": "ok", "database": "ok"}` |
| `/api/v1/system/health/live` | GET | None | System API liveness fallback | HTTP 200 `{"status": "ok"}` |
| `/api/v1/system/health/ready`| GET | None | System API readiness fallback| HTTP 200 `{"status": "ok"}` |
| `/api/v1/config` | GET | None | Public configuration | HTTP 200 with non-sensitive platform settings |
| `/api/v1/me` | GET | Bearer Token | Authenticated session check | HTTP 200 (user ID scrubbed from test logs) |
| `/api/v1/feed` | GET | None | Catalog discovery feed | HTTP 200 with valid items and timestamps |

## 3. Liveness vs. Readiness Isolation

To prevent cascading container restart loops:
- **Liveness** (`/healthz/live`): Validates only that the Python process and event loop are running. It does not query PostgreSQL, Redis, or external APIs.
- **Readiness** (`/healthz/ready`): Validates that critical operational dependencies are reachable. If PostgreSQL is disconnected, readiness returns HTTP 503 while liveness continues returning HTTP 200.

## 4. Execution Commands

### Local or CI Execution
```bash
# Automated deployment health check
export STAGING_API_URL="https://staging-api.example.com"
python scripts/staging/validate_deployment.py --base-url "$STAGING_API_URL"

# Comprehensive release smoke check
python scripts/release/smoke.py --base "$STAGING_API_URL"
```

### Expected Output Format
```text
[*] Validating deployment health against https://staging-api.example.com...
[PASS] /healthz/live -> 200 OK (duration: 14.2ms)
[PASS] /healthz/ready -> 200 OK (duration: 38.6ms)
[PASS] /api/v1/system/health/live -> 200 OK (duration: 12.1ms)
[PASS] /api/v1/system/health/ready -> 200 OK (duration: 36.4ms)
[*] Health validation complete. Result: PASS (Passed: 4/4)
[*] Report saved to reports/staging/deployment_report.json
```

## 5. Security & Credential Protection

Smoke test execution adheres to strict confidentiality rules:
- Authorization tokens are injected via environment variable `SMOKE_TEST_TOKEN` (never CLI arguments).
- Responses are checked for credential leaks (`password`, `postgresql://`, `redis://`, JWT signatures).
- User identifiers and merchant IDs are scrubbed from console output.
