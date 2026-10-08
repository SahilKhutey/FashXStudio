# AI Fashion Assistant — Production Build Foundation 7

## Capture UX + Profile Intelligence

Foundation 7 connects the server-side capture-quality engine to a user-facing retry/guidance contract and an Expo camera flow.

### Delivered
- `GET /api/v1/profile/me/photos/{photo_id}/guidance`
- deterministic guidance mapping from capture-quality reasons to user actions
- mobile Expo camera screen for try-on-reference capture
- direct upload to the signed object-storage URL
- async processing polling via the profile guidance endpoint
- ready/retry/processing states
- capture checklist overlay
- camera permission UX
- `expo-camera` integration
- API client + typed profile-media client
- Foundation 7 contract/unit tests

### Data/Privacy boundary
Raw image bytes still go directly to object storage. The mobile app receives only short-lived upload/access URLs and derived status/guidance. It never receives permanent object keys.

### Scope boundary
The client-side overlay is guidance, not a replacement for server validation. The server remains authoritative for `ready_for_tryon`.
