# AI Fashion Assistant — Production Build Foundation 4

## Scope

Foundation 4 adds the sensitive-media and consent boundary required before virtual try-on work:

- consent records are writable through the profile boundary;
- profile/try-on photos use direct signed object-storage uploads;
- uploaded media has an explicit `upload_pending -> processing -> accepted/rejected` lifecycle;
- completing an upload creates an asynchronous profile-photo processing job;
- internal services can request a short-lived, purpose-bound download URL for an accepted photo;
- raw media remains outside Postgres and is never returned as a permanent public URL.

## API surface

- `POST /api/v1/profile/consent`
- `POST /api/v1/profile/me/photos`
- `POST /api/v1/profile/me/photos/{photo_id}/complete`
- `GET /api/v1/profile/me/photos/{photo_id}`
- `POST /api/v1/profile/internal/media-access`

The internal media-access endpoint requires `X-Internal-Service-Token` and validates the photo-job relationship plus body-photo consent before issuing a short-lived signed URL.

## Storage contract

`ObjectStoragePort` is the application boundary. The R2 adapter uses S3-compatible presigned PUT/GET URLs. Storage SDK calls are executed off the async event loop with `asyncio.to_thread`.

## Async processing contract

Upload completion creates `profile_photo_jobs` and publishes a `profile-photo-processing` queue message. Foundation 4 defines the job contract; the actual pose/skin-tone worker is intentionally deferred to the next worker-focused build stage.

## Verification

- pytest: 27 passing
- Python compileall: passing
- Alembic offline migration chain through `0004_profile_media_jobs`: passing
- Ruff/mypy: expected to run in CI; execution depends on the development environment having the configured tools installed.
