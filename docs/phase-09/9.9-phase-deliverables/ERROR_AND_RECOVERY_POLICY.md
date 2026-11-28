# Error and Recovery Policy

- **API Client**: `mobile/src/api/client.ts` normalizes HTTP/network failures into `ApiError` with request correlation (`X-Request-ID`), aborts timed-out requests, and performs single-flight 401 token refresh on safe idempotent methods.
- **Network Connectivity**: `NetworkStatusBanner.tsx` and `useNetworkStatus.ts` surface offline state without crashing active screens.
- **Media & VTO**: `mapTryOnErrorCode()` maps backend VTO error codes to actionable user recovery prompts; camera permission denial offers an OS settings redirect rather than a dead end.
- **Lifecycle**: `useAppLifecycle.ts` and `useAndroidBackHandler.ts` guard background/foreground transitions and Android hardware back navigation.
