# FashXStudio System Map

## 1. Frontend Subsystem (Expo / React Native SDK 58)
- **Application Shell & Navigation**: `mobile/app/_layout.tsx`, `mobile/app/(tabs)/_layout.tsx`
- **Authentication**: `mobile/app/(auth)/`, `mobile/src/features/auth/`
- **Design System**: `mobile/src/design-system/` (semantic tokens, spacing, typography, elevation)
- **Feature Modules**:
  - `feed`: `mobile/app/(tabs)/feed.tsx`, `mobile/src/features/feed/`
  - `looks`: `mobile/app/(tabs)/looks.tsx`, `mobile/src/features/tryon/`
  - `closet`: `mobile/app/(tabs)/closet.tsx`, `mobile/src/features/wardrobe/`
  - `tryon`: `mobile/app/tryon/[jobId].tsx`
  - `garment`: `mobile/app/garment/[id].tsx`
  - `settings`: `mobile/app/settings/index.tsx`
  - `onboarding`: `mobile/app/onboarding/`

## 2. Backend Subsystem (FastAPI Modular Monolith)
- **Entrypoint**: `backend/fashx/main.py`
- **Security & Identity**: `backend/fashx/security/`, `backend/fashx/api/v1/me.py`
- **Catalog Acquisition & Ingestion**: `backend/fashx/catalog/acquisition/`
- **Discovery & Personalization**: `backend/fashx/discovery/`, `backend/fashx/recommendation/`
- **Virtual Try-On Orchestration**: `backend/fashx/tryon/`, `backend/fashx/infrastructure/tryon/`
- **Wardrobe & Affiliate Commerce**: `backend/fashx/commerce_wardrobe/`
- **Frozen Modules** (ADR-0001): `backend/fashx/api/v1/{cart,checkout,payments,orders,...}` (gated)

## 3. Infrastructure & Persistence
- **Primary Database**: PostgreSQL 16 + pgvector (local fallback: SQLite `fashx_local.db`)
- **Queue / Cache**: Redis 7 + Celery
- **Object Storage**: S3-compatible (local development: local file directory storage)
- **AI Inference**: FASHN Hosted API adapter (`fashn_api`) / local testing `MockAdapter`
