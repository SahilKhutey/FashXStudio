# RC05 — 09 Mobile Integration

## Objective
Connect and verify the mobile application virtual try-on screens and hooks against real backend API contracts, ensuring that all UI states, polling behavior, error handling, and mock disclosures operate seamlessly.

## Existing State
- Mobile job screen: `mobile/app/tryon/[jobId].tsx`
- Hooks: `useJob`, `useStartTryOn`, `useRetryTryOn`, `useTryOnFeedback`
- Polling interval helper: `mobile/src/features/tryon/polling.ts`

## Changes
- Verified complete state machine coverage in `mobile/app/tryon/[jobId].tsx`:
  - `queued`: Loading spinner and "Queued in processing pipeline" label.
  - `processing` / `quality_check`: Real progress indicator with pipeline phase subtitles.
  - `completed`: Result image rendering, before/after comparison toggle, wardrobe save, feedback chips.
  - `failed` / `cancelled`: Clear error reason, "Try again" retry button generating a fresh idempotency key.
  - `mock`: Unmistakable warning banner `⚠️ Preview only: not a real try-on` displayed whenever `job.provider === "mock"`.
- Verified polling backoff: intervals scale from 2s during active inference up to 10s if delayed, disabling polling in background.

## UI State Mapping Matrix
| Backend Status | Mobile UI State | Visual Representation |
|---|---|---|
| `queued` | Queued | Activity indicator with queued text |
| `preprocessing` | Processing | Pipeline step indicator |
| `inference` | Processing | Pipeline step indicator |
| `quality_check` | Quality Check | Safety & realism validation notice |
| `postprocessing` | Processing | Watermarking and saving notice |
| `completed` | Completed | Result image with before/after toggle |
| `failed` | Failed | Error banner with retry action |
| `cancelled` | Cancelled | Cancellation notice with back button |

## Implementation
```tsx
// mobile/app/tryon/[jobId].tsx
const isCompleted = job.status === "completed";
const isFailed = job.status === "failed" || job.status === "cancelled";
const isInProgress = !isCompleted && !isFailed;
const isMockProvider = job.provider === "mock";

{isMockProvider && (
  <View style={styles.mockBanner}>
    <Text style={styles.mockBannerText}>⚠️ Preview only: not a real try-on</Text>
  </View>
)}
```

## Execution
```bash
npm --prefix mobile test -- tryon
npm --prefix mobile run typecheck
```

## Tests
- `tryon_screen.test.tsx` -> 8 passed in 2.55s
- `tryon_polling.test.ts` -> 9 passed
- `tryon_feedback.test.ts` -> 7 passed
- Full mobile Jest suite -> 21/21 suites passed, 152/152 tests passed
- TypeScript typecheck -> 0 errors

## Risks
- Client polling indefinitely if job becomes stuck.
- Mitigation: Polling helper detects timeouts exceeding 120s and renders a user-friendly "taking longer than usual" advisory.

## Evidence
```
Test Suites: 21 passed, 21 total
Tests:       152 passed, 152 total
Time:        11.076 s
TypeScript:  0 errors
```

## Exit Criteria
- Mobile try-on journey fully operational and tested against API schemas.
