# VTO Submission API

- Reuses `useStartTryOn` (`mobile/src/features/tryon/useTryOn.ts`) and `submitTryOnJob` (`mobile/src/features/tryon/tryonApi.ts`) sending `POST /api/v1/tryon/jobs` with stable `Idempotency-Key` headers.
