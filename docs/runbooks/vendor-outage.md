# Third-Party Try-On Vendor Outage Runbook

## 1. Overview & Failure Modes

FashXStudio leverages licensed virtual try-on providers (e.g., FASHN API / Modal self-hosted Apache-2.0 worker).
When the external provider suffers degradation or downtime:
- **System Isolation**: `/healthz/ready` deliberately DOES NOT check external try-on providers. An external outage is an application-level degraded state, NOT a container-level failure. ECS containers must NOT be killed by the load balancer.
- **Circuit Breaker**: The internal circuit breaker (`backend/fashx/ml/breaker.py`) automatically trips after 5 consecutive 5xx/timeout errors from the vendor, preventing worker queue exhaustion and runaway retries.

---

## 2. Immediate Containment (First 15 Minutes)

1. **Verify Vendor Status**:
   - Check FASHN status page and query recent Celery tryon error logs.
   - If error rate > 15% or 5 consecutive jobs fail, `TryOnFailureRateHigh` alarm triggers.
2. **Activate Try-On Kill Switch**:
   - Flip the feature flag to disable new try-on job submissions without restarting containers:
     ```bash
     curl -X POST https://api.fashx.studio/api/v1/admin/feature-flags \
       -H "Authorization: Bearer $ADMIN_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"name": "tryon_enabled", "enabled": false, "reason": "FASHN API upstream 503 outage"}'
     ```
3. **User Experience Behavior**:
   - Mobile client receives `409 Conflict` or `503 Service Unavailable` with machine-readable error `TRYON_SERVICE_TEMPORARILY_DEGRADED`.
   - The app surfaces an in-app banner: *"Virtual dressing room is currently undergoing scheduled maintenance. You can still browse and save outfits to your closet."*
   - Discovery feed, wardrobe, and buying links remain 100% operational.

---

## 3. Resolution & Recovery

1. **Monitor Vendor Recovery**:
   - Test external vendor endpoint with synthetic test garment and mock silhouette.
2. **Drain / Re-queue Backlogged Jobs**:
   - Completed or failed jobs are logged in `tryon_usage(outcome='failed', error_code='PROVIDER_5XX')`.
   - Clean up expired job state in Redis.
3. **Re-enable Kill Switch**:
   ```bash
   curl -X POST https://api.fashx.studio/api/v1/admin/feature-flags \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "tryon_enabled", "enabled": true, "reason": "Upstream provider confirmed stable"}'
   ```
4. Verify end-to-end try-on flow in staging before notifying users.
