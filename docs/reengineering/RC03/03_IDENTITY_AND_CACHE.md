# RC-03 — Identity & Cache Isolation Architecture

## Context & Problem Definition (BP-01 / P0)
Prior to RC-03, mobile TanStack Query hooks utilized static, un-scoped query keys such as `["feed"]` and `["tryon", "jobs", limit]`. When a user signed out or swapped accounts, stale cached data belonging to User A remained in memory and was rendered to User B.

## Implementation Architecture

### 1. Centralized User-Scoped Query Keys
All React Query cache keys are centralized in `mobile/src/app-shell/queryKeys.ts`:

```typescript
export const queryKeys = {
  me: (userId: string | null) => ["me", userId] as const,
  feed: (userId: string | null) => ["feed", userId] as const,
  garment: (userId: string | null, garmentId: string) =>
    ["garment", userId, garmentId] as const,
  wardrobe: (
    userId: string | null,
    limit: number,
    offset: number
  ) => ["wardrobe", userId, limit, offset] as const,
  tryOnJobs: (userId: string | null, limit: number) =>
    ["tryon", "jobs", userId, limit] as const,
  tryOnJob: (userId: string | null, jobId: string | null) =>
    ["tryon", "job", userId, jobId] as const,
  derivedProfile: (userId: string | null) =>
    ["derivedProfile", userId] as const,
};
```

### 2. Cache Invalidation and Identity Lifecycle
In `mobile/src/features/auth/authStore.ts`, state mutations are bound to query client cache invalidation:
1. **Account Switch**: When `setMe(user)` detects a changed `user_id` (`previousUserId !== nextUserId`), it executes `queryClient.clear()`.
2. **Sign-Out**: When `signOut()` is called:
   - `queryClient.clear()` flushes all in-memory React Query caches.
   - `Image.clearDiskCache()` purges downloaded photo thumbnails from disk.
   - Dev tokens and session credentials are removed from local storage.
   - Zustand auth state resets to null.

### 3. Verification Evidence
Unit test `mobile/src/app-shell/__tests__/queryKeys.test.ts` verified that each query key function isolates cache keys across distinct user identifiers (7 passed).
