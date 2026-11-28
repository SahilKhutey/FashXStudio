# VTO Job Experience

- **Submission & Idempotency**: `submitTryOnJob()` (`mobile/src/features/tryon/tryonApi.ts`) posts to `/api/v1/tryon/jobs` with an `Idempotency-Key` header.
- **Status Lifecycle & Cancellation**: `getTryOnJob()` polls job status (`queued`, `processing`, `succeeded`, `failed`, `cancelled`) and `cancelTryOnJob()` posts to `/api/v1/tryon/jobs/{jobId}/cancel`.
- **Error Mapping & Simulation Notice**: `mapTryOnErrorCode()` (`mobile/src/features/tryon/errors.ts`) translates 16 backend VTO error codes (including `VTO_CONSENT_REQUIRED`, `PERSON_NOT_DETECTED`, `GARMENT_PROCESSING_NOT_AUTHORIZED`) into clear user messages, while `VisualSimulationNotice.tsx` labels generated outputs as visual simulations.
- **Verification**: `phase09_6_vto.test.tsx` and `phase09_9_exit_gate.test.tsx` pass locally; live provider execution is `PENDING`.
