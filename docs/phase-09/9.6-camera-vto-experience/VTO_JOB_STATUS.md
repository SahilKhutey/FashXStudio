# VTO Job Status

- `mobile/src/features/tryon/polling.ts` (`getTryOnPollInterval`, `isTerminalTryOnStatus`) and `mobile/app/tryon/[jobId].tsx` poll `GET /tryon/jobs/{jobId}` only while the screen is focused and stop on terminal states (`completed`, `failed`, `cancelled`).
