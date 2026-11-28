# Result Access Security

- Backend `backend/fashx/tryon/router.py` enforces authenticated principal ownership on `/tryon/jobs`, `/tryon/jobs/{jobId}`, `/tryon/jobs/{jobId}/feedback`, and `/tryon/artifacts/{artifactKey}`.
- Cross-account ownership tests (`404`/`403`) run in backend CI against Postgres.
