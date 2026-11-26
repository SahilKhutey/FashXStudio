# 18 — Release Readiness Checklist

| Item | Status | Notes |
|---|---|---|
| Body vs garment basis separation (`measurement_matcher.py`) | Implemented & tested | `GARMENT` rejected by body matcher |
| Versioned category policies (`category_policy.py`) | Implemented & tested | Only `TSHIRTS` enabled by default (`v1.0`) |
| Sourced ease governance (`ease_policy.py`) | Implemented & tested | Default registry empty; no invented ease |
| Merchant & chart revision isolation | Implemented & tested | Offer/merchant mismatch fails as `CONFLICTING_DATA` |
| First-class missing/stale/conflict abstentions | Implemented & tested | Returns `200` abstention statuses cleanly |
| Internal confidence & hard gate precedence | Implemented & tested | `display_to_shopper = False` until calibrated |
| Non-guarantee copy & VTO separation | Implemented & tested | `fit_guaranteed = False`; VTO raises `FitEvidenceSecurityError` |
| Snapshot persistence & invalidation (`0058`) | Implemented | Chart update & profile change invalidate snapshots |
| Shopper feedback ownership, dedup & deletion | Implemented & tested | Bound strictly to recommendation snapshot |
| Evaluation dataset schema & metrics | Implemented & tested | Split-leakage guard & calibration bins built |
| Live Postgres migration round-trip (`0058`) | Pending CI | Local Windows lacks Postgres/Docker (Rule 14) |
| Manually labelled real-world dataset evaluation | Pending human collection | Required before production accuracy sign-off (Rule 2) |
| Live staging verification | Pending staging | Outside local workspace scope |
