# AI Fashion Assistant — Foundation 8

## Profile Intelligence

Foundation 8 introduces versioned profile artifacts, derived skin-tone results, profile readiness, and the skin-tone processing queue. Raw photos remain object-storage references; derived skin-tone data is stored separately and is never treated as raw biometric media.

### Contracts
- `GET /api/v1/profile/me/readiness`
- `GET /api/v1/profile/me/artifacts/latest`
- `GET /api/v1/profile/{user_id}/derived`
- `[internal] POST /api/v1/profile/internal/skin-tone-jobs/{job_id}/complete`

### Profile readiness
A profile is `ready_for_tryon` when a complete body profile exists and an accepted try-on reference photo has passed capture-quality validation. Skin tone is separately tracked as a personalization readiness signal and is not required to start the V1 try-on job.

### Skin tone
The worker estimates ITA from a face crop using a deterministic OpenCV/PIL pipeline. The result carries a confidence value, method and version. Low-confidence/no-face results remain incomplete rather than inventing a classification.

### Migration
`0007_profile_intelligence` adds `skin_tone_results` and `profile_artifacts`.
