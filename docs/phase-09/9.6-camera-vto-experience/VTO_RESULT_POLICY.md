# VTO Result Policy

- Result URLs are retrieved via authenticated `GET /tryon/jobs/{jobId}` / `GET /tryon/artifacts/{artifactKey}` (`backend/fashx/tryon/router.py`), never public storage keys.
