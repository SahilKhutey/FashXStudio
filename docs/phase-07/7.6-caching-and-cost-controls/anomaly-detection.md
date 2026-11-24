# Spend Anomaly Detection & Runaway Loop Protection

## 1. Operational Threat Vectors

In automated cloud environments, inference cost blowups typically result from:
1. **Infinite Worker Retry Loops**: A worker repeatedly catching an uncaught exception and retrying the paid inference step.
2. **Catalog Crawling / Scraping Bots**: External bot accounts iterating through product IDs requesting try-on renders at high concurrency.
3. **Misconfigured Batch Jobs**: An internal staging test script launching 10,000 requests against the live production provider.

---

## 2. Spend Velocity Analysis

The `TryOnAnomalyDetector` continuously tracks spend velocity:

$$\text{Velocity Ratio} = \frac{\text{Spend in Recent Window (last 15m)}}{\text{Spend in Baseline Window (previous 60m / 4)}}$$

### Rules:
- If `Velocity Ratio >= 3.0` and absolute spend is material ($> \$25$):
  - Emits `SPEND SURGE DETECTED` high-priority warning.
  - Automatically throttles non-interactive background workers.
  - Requires explicit operator clearance or auto-resets after window cools down.

---

## 3. Worker Execution Guardrails

In addition to spend velocity, the following circuit breakers prevent worker runaways:
- **Maximum 3 Retries Per Job**: Non-retryable errors fail immediately without retry.
- **Provider Request ID Tracking**: If a job attempt already generated a `provider_request_id`, it is never re-submitted blindly; instead, the status is polled.
- **Worker Lease Heartbeats**: A crashed worker's lease expires in 120 seconds, preventing stale processes from resuming stale work.
