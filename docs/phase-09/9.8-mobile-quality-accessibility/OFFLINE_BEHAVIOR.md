# Offline Behavior

- `useNetworkStatus` (`mobile/src/hooks/useNetworkStatus.ts`) and `NetworkStatusBanner` (`mobile/src/components/NetworkStatusBanner.tsx`) surface a polite `accessibilityRole="alert"` banner when offline without treating unknown reachability (`null`) as offline.
