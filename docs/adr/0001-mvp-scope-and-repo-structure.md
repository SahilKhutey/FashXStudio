# ADR-0001: MVP scope cut and repository structure

- **Status:** Accepted
- **Date:** 2026-10-04
- **Owner:** Sahil Khutey

## Context
The repo grew a full e-commerce backend (inventory, cart, checkout, payments, fulfilment, returns) before the headline feature (virtual try-on) ran on a real model. The strategy is to redirect to existing merchants via affiliate links, not to operate commerce.

## Decision
1. **MVP = styling + discovery + virtual try-on + closet + affiliate redirect + fit feedback.**
2. C05-C11 and F11-F13 are **frozen**: kept in git, not extended, not mounted in the production router, excluded from release gates.
3. One backend root, one mobile root, one docs tree (structure below).
4. Documentation claims must be backed by CI. `docs/STATUS.md` is the single source of truth; README badges are CI-generated only.
5. Repo is private until license and positioning decisions are made.

## Target structure
```
FashXStudio/
├─ README.md  LICENSE  CONTRIBUTING.md  Makefile  pyproject.toml  alembic.ini  .env.example
├─ backend/fashx/            # ONE python package root (merge api/ + app/)
│  ├─ api/                   # routers, middleware, error envelopes
│  ├─ application/           # use cases
│  ├─ domain/                # pure domain (+ frozen/ subpackage)
│  ├─ infrastructure/        # repositories, adapters (tryon, storage, vlm, affiliate)
│  └─ platform/              # event bus, outbox, observability, security
├─ workers/                  # celery workers (photo, skin tone, try-on)
├─ ml/                       # model wrappers, eval sets (no weights in git)
├─ mobile/                   # ONE Expo app (merge apps/mobile)
├─ schemas/  database/  infra/  scripts/  tests/
└─ docs/  STATUS.md  product/  architecture/  adr/  design/  logs/  archive/
```

## Consequences
- Smaller surface to secure, test and explain.
- Frozen code stays recoverable; no history rewrite.
- Code moves happen on a branch, one move per commit, with the test suite as the safety net.
