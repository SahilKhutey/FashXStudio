# User / Shopper Rate Limiting & Concurrency Controls

## 1. Rate Limit Rules

To prevent resource exhaustion, automated scraping, or accidental shopper spamming, three complementary limits govern shopper activity:

| Limit Type | Threshold | Window Duration | Purpose |
|---|---|---|---|
| **Burst Window** | 5 Requests | 10 Minutes (600s) | Prevents rapid-fire button clicking. |
| **Daily Ceiling** | 20 Requests | 24 Hours (86400s) | Protects platform unit economics per user. |
| **Concurrency Ceiling** | 2 In-Flight Jobs | Real-time | Blocks parallel worker swarm by a single user. |

---

## 2. Distributed Sliding Window Implementation

Rate limits are evaluated using Redis Sorted Sets (`ZSET`) via an atomic Lua script:
- Scores store request timestamps.
- Elements older than $(now - window)$ are evicted with `ZREMRANGEBYSCORE`.
- `ZCARD` counts remaining active requests.
- If under limit, current request is added and TTL is updated.
- If exceeded, the script inspects the oldest timestamp to compute exact seconds until reset (`Retry-After`).

---

## 3. HTTP 429 Response Format

When a rate limit or concurrency ceiling is reached, the API terminates processing immediately before touching PostgreSQL or queuing tasks:

**HTTP Status**: `429 Too Many Requests`

**HTTP Headers**:
```http
Retry-After: 45
X-RateLimit-Limit: 5
X-RateLimit-Type: USER_BURST_10M
```

**JSON Response Body**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "You have requested too many try-on generations recently. Please try again shortly.",
  "limit_type": "USER_BURST_10M",
  "retry_after_seconds": 45
}
```
