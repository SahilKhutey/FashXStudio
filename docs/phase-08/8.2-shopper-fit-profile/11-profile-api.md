# 11 — Authenticated Fit Profile API Specification

All routes are mounted under `/api/v1/profile/fit` with default-deny `Depends(get_principal)` authentication. Shopper identity is always resolved from `principal.user_id`.

| Method | Path | Purpose | Error Semantics |
|---|---|---|---|
| `GET` | `/api/v1/profile/fit` | Retrieve profile & category readiness | Returns `PROFILE_INCOMPLETE` when empty |
| `POST` | `/api/v1/profile/fit/measurements` | Batch add body measurements | 403 missing consent; 422 invalid input |
| `PATCH` | `/api/v1/profile/fit/measurements/{field}` | Update measurement | 409 version mismatch; 404 not found; 403/422 |
| `POST` | `/api/v1/profile/fit/measurements/{field}/confirm` | Confirm aged/unusual value | 403/404 |
| `DELETE` | `/api/v1/profile/fit/measurements/{field}` | Delete one measurement | 404 if absent |
| `GET` | `/api/v1/profile/fit/measurements/history` | List authorized change history | Owner-scoped |
| `PUT` | `/api/v1/profile/fit/preferences` | Set default preference & display unit | Validated enum |
| `PUT` | `/api/v1/profile/fit/preferences/{category}` | Set category fit preference | 422 unknown category |
| `DELETE` | `/api/v1/profile/fit/preferences/{category}` | Clear category fit preference | 404/422 |
| `GET` | `/api/v1/profile/fit/policies/{category}` | Category requirement guidance | 404 unsupported category |
| `GET` | `/api/v1/profile/fit/definitions` | List measurement guidance registry | Authenticated read |
| `GET` | `/api/v1/profile/fit/consents` | Purpose-specific consent statuses | Authenticated read |
| `PUT` | `/api/v1/profile/fit/consents/{purpose}` | Grant or withdraw purpose consent | 403 under-18 rejection |
| `DELETE` | `/api/v1/profile/fit` | Delete all fit profile data | Cascades & revokes consent |
