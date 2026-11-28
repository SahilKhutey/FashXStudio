# Memory Management

- Avoids storing base64 photos or permanent signed URLs in Zustand; uses `expo-image` bounded caching and `Image.clearDiskCache()` on sign-out (`mobile/src/features/auth/authStore.ts`).
