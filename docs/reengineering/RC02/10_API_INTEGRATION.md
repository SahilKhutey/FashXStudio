# RC-02 — API Integration & Contract Verification

## Network & Client Configuration
The mobile API client ([`mobile/src/api/client.ts`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/api/client.ts)) provides resilient HTTP communication with the backend:
- **Base URL Resolution**: Defaults to `http://localhost:8000` or `EXPO_PUBLIC_API_URL` environment setting.
- **Authorization Headers**: Attaches `Authorization: Bearer <token>` automatically on every authenticated request.
- **Error Normalization**: Maps HTTP status codes to typed `ApiError` instances.
- **Automatic Token Refresh**: Transparently retries once upon receiving `401 Unauthorized` for active Supabase sessions.

## Verified Endpoints Consumed by Mobile Application

| Endpoint | Method | Hook / Component | Contract & Schema |
| :--- | :--- | :--- | :--- |
| `/api/v1/feed` | `GET` | `useFeed()` (`feed.tsx`, `explore.tsx`) | `FeedResponse` with `items`, `empty_reason`, `relaxed` |
| `/api/v1/feed/signals` | `POST` | `useSignal()` (`feed.tsx`) | `FeedSignalRequest` (`garment_id`, `action`) |
| `/api/v1/wardrobe/items` | `GET` | `useUserWardrobe()` (`closet.tsx`) | `UserWardrobeItem[]` |
| `/api/v1/wardrobe/items` | `POST` | `useSaveToWardrobe()` (`feed.tsx`, `explore.tsx`, `garment/[id].tsx`, `tryon/[jobId].tsx`) | `SaveWardrobeResponse` |
| `/api/v1/wardrobe/items/{id}` | `DELETE` | `useRemoveFromWardrobe()` (`closet.tsx`) | `204 No Content` |
| `/api/v1/garments/{id}` | `GET` | `useGarmentDetail()` (`garment/[id].tsx`) | `CustomerGarmentDetailResponse` |
| `/api/v1/tryon/jobs` | `POST` | `useStartTryOn()` (`garment/[id].tsx`) | `TryOnJobCreateResponse` |
| `/api/v1/tryon/jobs/{id}` | `GET` | `useJob()` (`tryon/[jobId].tsx`) | `TryOnJobResponse` |
| `/api/v1/tryon/jobs` | `GET` | `useTryOnJobs()` (`looks.tsx`) | `TryOnJobListResponse` |
| `/api/v1/tryon/jobs/{id}/feedback` | `POST` | `useTryOnFeedback()` (`tryon/[jobId].tsx`) | Feedback payload with rating & issue tags |
| `/api/v1/me` | `GET` | `useAuthStore` | User profile, roles, and onboarding status |
