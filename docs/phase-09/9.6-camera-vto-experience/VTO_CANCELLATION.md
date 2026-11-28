# VTO Cancellation

- `cancelTryOnJob(jobId)` (`mobile/src/features/tryon/tryonApi.ts`) and `useCancelTryOn()` (`mobile/src/features/tryon/useTryOn.ts`) issue `POST /tryon/jobs/{jobId}/cancel` and update the TanStack Query job cache from the server response.
