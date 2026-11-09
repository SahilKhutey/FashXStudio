# RC12: Deployment, Migrations and Rollback Procedures

## 1. Release Invariants
- Immutable build containers with cryptographic commit SHA tags.
- Environment configurations strictly separated between `local`, `test`, `staging`, and `production`.
- Zero database migrations deployed without verified rollback procedures (`alembic upgrade head; downgrade -1; upgrade head`).

## 2. Rollback Runbook
If an unhandled regression or stability crash occurs post-deployment:
1. **Traffic Rollback**:
   - Revert traffic routing in API gateway/load balancer to previous container SHA.
2. **Feature Kill Switch**:
   - If regression is localized to try-on or recommendations, set `vto_real.enabled = False` in [`backend/fashx/core/release_policy.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/release_policy.py).
3. **Database Reversion**:
   - If schema rollback is strictly required, run `python -m alembic downgrade -1` after verifying snapshot restore points.
4. **Mobile Fallback**:
   - Trigger app cache invalidation and surface maintenance banner.
