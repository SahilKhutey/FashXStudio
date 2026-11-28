# Network Resilience

- `queryClient` (`mobile/src/app-shell/queryClient.ts`) retries only retryable `ApiError` queries up to 2 times and keeps `mutations.retry: false` to prevent duplicate VTO submissions.
