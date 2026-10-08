# Foundation 14 — Try-On Input Assembly & Provider Runtime

## Goal
Make the asynchronous VTO path executable without coupling the product to a specific model vendor.

## Runtime flow

1. Try-On job is atomically claimed.
2. Profile service provides the accepted try-on reference metadata.
3. Catalog service provides a supported garment + compatible image.
4. The worker creates short-lived signed input URLs.
5. `TryOnProvider` submits the job to the configured provider.
6. Provider completion is polled.
7. The result image is downloaded and uploaded to `tryon-results/<artifact_key>.jpg`.
8. The internal Try-On API marks the job completed and creates the artifact record.

## Provider rule
`TRYON_PROVIDER=disabled` is the default. `TRYON_PROVIDER=http` enables the generic HTTP adapter only when a commercially approved VTO endpoint is configured. No research checkpoint is embedded or implicitly authorized.

## Supported MVP categories
Only tops and dresses are accepted by the current VTO input validator. Shoes, accessories, sarees, lehengas, dupattas, and complex layering remain outside the MVP contract.

## Security
- Input URLs are short-lived signed R2 URLs.
- Result objects remain private and are served through short-lived signed URLs.
- Provider API credentials are read only from typed settings.
- The mobile client never receives storage keys.

## Verification
Foundation 14 tests cover category gating, execution contracts, and the fail-closed provider boundary.
