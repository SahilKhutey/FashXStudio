# RC05 — 13 Execution Guide

## Objective
Provide step-by-step operational instructions for configuring, launching, and verifying the Virtual Try-On pipeline in development, staging, and production environments.

## Environment Configuration
Configure backend environment in `.env`:
```ini
# Core Configuration
ENV=dev
APP_ENV=development
AUTH_MODE=local
AUTH_JWT_SECRET=<ci-test-jwt-secret-min-32-chars>
DATABASE_URL=postgresql+asyncpg://fashx:fashx@localhost:5432/fashx_test
REDIS_URL=redis://localhost:6379/0

# Storage Configuration
STORAGE_BACKEND=local
LOCAL_STORAGE_DIR=./.local_storage

# Provider Configuration (Mock Development)
TRYON_PROVIDER=mock

# Provider Configuration (Hosted Commercial Inference)
# TRYON_PROVIDER=fashn_api
# FASHN_API_KEY=<provider-key-placeholder>
# FASHN_MODEL=tryon-v1.6
```

## Running the Services
1. **Database & Infrastructure (Docker Compose):**
   ```bash
   docker compose up -d postgres redis
   ```
2. **Apply Database Migrations:**
   ```bash
   alembic upgrade head
   ```
3. **Start FastAPI Backend:**
   ```bash
   uvicorn fashx.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. **Start Background Worker:**
   ```bash
   celery -A fashx.workers.app.app worker --loglevel=info -Q tryon,ingest
   ```
   *Alternative polling worker without Celery:*
   ```bash
   python -m fashx.tryon.application.worker
   ```
5. **Configure Mobile LAN Target:**
   ```bash
   python scripts/mobile/configure_lan_api.py --apply
   ```
6. **Start Mobile Expo Application:**
   ```bash
   cd mobile
   npx expo start --clear
   ```

## Verifying the Pipeline
Run the automated end-to-end smoke verification script:
```bash
python scripts/rc05_vto_smoke.py
```
Expected output:
```
=== FashXStudio RC-05 Virtual Try-On Smoke Verification ===
[1/8] Verifying Health & Readiness probes... OK
[2/8] Authenticating User A and User B... OK
[3/8] Submitting try-on job for User A with Idempotency-Key... OK
[4/8] Executing VTO pipeline... OK
[5/8] Polling job status and validating signed artifact URL... OK
[6/8] Verifying User B cannot access User A's try-on job or artifact... OK
[7/8] Saving completed try-on look to user wardrobe... OK
[8/8] Submitting post-try-on visual accuracy and fit feedback... OK
============================================================
SUCCESS: ALL RC-05 VIRTUAL TRY-ON SMOKE WORKFLOWS VERIFIED
============================================================
```

## Troubleshooting
- **Redis Connection Refused:** If Redis is down, the API falls back to database-persisted queueing without blocking the HTTP client. Start Redis or use database-polling workers.
- **Mock Watermark Visible:** Expected in development. To run genuine AI inference, configure `TRYON_PROVIDER=fashn_api` and supply valid `FASHN_API_KEY`.
- **403 Forbidden on Artifact:** Requesters must be authenticated and own the corresponding try-on job.
