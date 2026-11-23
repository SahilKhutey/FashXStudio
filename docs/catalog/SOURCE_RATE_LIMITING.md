# Source Rate Limiting Architecture

## 1. Objectives

To respect external retailer terms of service, protect upstream partner infrastructure, and avoid IP bans or rate limit lockouts, FashXStudio enforces strict rate limiting per catalog source.

## 2. Distributed Token Bucket Limiter

Implemented in `backend/fashx/catalog/acquisition/rate_limiter.py`:
- **Token Bucket Algorithm**: Each source key maintains an independent bucket replenished at `max_rps` tokens per second.
- **Burst Capacity**: Allows immediate burst up to the configured limit, while smoothly throttling sustained throughput.
- **Asynchronous Non-blocking Sleep**: If insufficient tokens are available, the acquiring task asynchronously sleeps for the required interval (`needed / max_rps`) without blocking event loop threads.

```python
class DistributedRateLimiter:
    async def acquire(self, key: str, max_rps: float) -> float: ...
    async def record_retry_after(self, key: str, seconds: float) -> None: ...
```

## 3. Dynamic 429 Retry-After Handling

When an upstream source returns an HTTP 429 Too Many Requests response:
1. The adapter or transport inspects the `Retry-After` header.
2. If numeric seconds or an HTTP date is present, `record_retry_after(key, seconds)` locks the rate limiter bucket for that source until `now + seconds`.
3. Subsequent requests for that source automatically wait until the lock expires, avoiding cascading failure or provider account suspension.
