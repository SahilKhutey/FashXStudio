# 01 — Feed Architecture

- `mobile/app/(tabs)/feed.tsx` uses `useFeed()` (`mobile/src/features/feed/hooks.ts`) connected to `/api/v1/feed` with `FlashList`, cursor pagination, impression tracking (`useImpressionTracker`), and signal feedback (`useSignal`).
