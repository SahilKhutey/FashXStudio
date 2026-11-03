# RC-00 Runtime Validation

## Matrix of Verifications

| Check Item | Environment | Verified Status | Evidence |
| :--- | :--- | :--- | :--- |
| **Python Environment** | Windows / Python 3.12.10 | **PASS** | `.venv` active with required packages |
| **Backend Initialization** | Localhost (:8000) | **PASS** | `GET /` returns `{"service": "AI Fashion Assistant API", "status": "ok"}` |
| **Health Endpoints** | Localhost (:8000) | **PASS** | `GET /healthz/live` and `ready` respond 200 |
| **OpenAPI Schema** | Localhost (:8000) | **PASS** | 222 registered endpoints extracted |
| **Auth Verification** | Localhost (:8000) | **PASS** | `GET /api/v1/me` succeeds with minted dev token |
| **Feed Endpoint** | Localhost (:8000) | **PASS (Empty)** | `GET /api/v1/feed` returns 200 with 0 candidates |
| **Closet Endpoint** | Localhost (:8000) | **PASS (Empty)** | `GET /api/v1/wardrobe/items` returns 200 with `[]` |
| **Database Migrations** | Local SQLite (`fashx_local.db`) | **PASS** | 32 migrations applied up to `0032_tryon_feedback_issue_tags` |
| **Mobile Jest Tests** | Node 20 / Jest 30 | **PASS** | 18 suites / 133 tests passed in 7.95s |
| **Unit Adapter Tests** | Pytest 8.4.2 | **PASS** | 27 tests passed in 9.17s |
| **Audit Toolkit Tests** | Pytest 8.4.2 | **PASS** | 6 tests passed in 0.08s |
| **PostgreSQL & Redis** | Docker Containers | **BLOCKED** | Docker daemon not running in current local session |
| **Physical Android App** | Physical Device | **BLOCKED** | Requires physical device tethering on Wi-Fi |
