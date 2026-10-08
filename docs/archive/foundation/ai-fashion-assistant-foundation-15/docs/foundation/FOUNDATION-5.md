# AI Fashion Assistant — Production Build Foundation 5

## Scope
Foundation 5 implements the first production worker execution path for profile photos.

## Implemented
- Redis queue consumer for `profile-photo-processing`.
- Atomic job claim with stale-processing recovery.
- Deterministic image validation using Pillow.
- Basic person-presence pre-gate for try-on reference images using OpenCV HOG.
- Basic face-presence gate for skin-tone images using OpenCV Haar detection.
- SHA-256 content hashing.
- Image metadata persistence.
- Retryable vs terminal failure handling.
- Maximum-attempt limit and dead-letter queue.
- Profile Service internal claim/complete/fail callbacks.
- Worker-only internal authentication through `X-Internal-Service-Token`.

## Boundary
This is a **pre-CV/ML quality gate**, not the final pose-landmark validator. A future MediaPipe/TFLite pose adapter can replace the OpenCV person detector without changing the queue/job contract.

## Run locally
```bash
make profile-photo-worker
```

The API must be running and `INTERNAL_SERVICE_TOKEN`/R2 configuration must be present for real queue execution.
