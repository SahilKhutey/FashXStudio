# FashXStudio

**AI personal stylist with virtual try-on.** Build a profile once, get a personalized fashion feed from multiple merchants, see outfits on your own body, save to a closet, and buy through the merchant.

> **Status: pre-pilot.** See [docs/STATUS.md](docs/STATUS.md) for what is real, mocked, and frozen.

## MVP scope
1. **Profile:** photo quality gate, skin tone/undertone, body measurements, style preferences, consent.
2. **Catalog:** multi-merchant ingest, normalization, dedup, attribute enrichment.
3. **Discovery:** hard filter, compatibility scoring, diversity ranking, with "why this suits you".
4. **Virtual try-on:** async jobs, swappable model adapters, watermarking, cache.
5. **Closet and buy:** price-snapshot closet, tracked affiliate redirect, fit feedback.

Commerce operations (inventory, cart, checkout, payments, fulfilment, returns) are **frozen**, post-MVP. See [ADR-0001](docs/adr/0001-mvp-scope-and-repo-structure.md).

## Architecture
Modular monolith with clean layering (router, use case, pure domain, repository, adapters). FastAPI, PostgreSQL + pgvector, Redis/Celery, Cloudflare R2/S3, Expo (React Native). Decisions live in [docs/adr](docs/adr).

## Quickstart (Windows PowerShell)
```powershell
Copy-Item .env.example .env
docker compose up -d postgres redis
python -m alembic upgrade head
$env:PYTHONPATH = ".;api"
python -m pytest tests -q -p no:cacheprovider
python -m uvicorn api.app.main:app --reload --port 8000
```
macOS/Linux: use `export PYTHONPATH=".:api"`.
Mobile: `cd mobile && npm install && npx expo start`

## Docs
[Status](docs/STATUS.md) · [Product](docs/product) · [Architecture](docs/architecture) · [ADRs](docs/adr) · [Design](docs/design) · [Logs](docs/logs)

## License
Proprietary. See [LICENSE](LICENSE).
