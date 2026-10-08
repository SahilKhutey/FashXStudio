# ADR-0001: MVP scope cut and repository structure

- **Status:** Accepted · **Date:** 2026-10-04 · **Owner:** Sahil Khutey

## Context
The repo grew a full commerce backend (inventory, cart, checkout, payments, fulfilment, returns) before the headline feature (virtual try-on) ran on a real model. The strategy is to redirect to existing merchants via affiliate links, not to operate commerce.

## Decision
1. MVP = styling + discovery + virtual try-on + closet + affiliate redirect + fit feedback.
2. C05-C11 and F11-F13 are frozen: kept in git, not extended, to be unmounted from the production router (Phase 2), excluded from release gates.
3. One backend root, one mobile root, one docs tree.
4. Claims must be backed by CI and measurement; docs/STATUS.md is the source of truth; no hand-written badges.
5. Repo stays private until license and positioning are decided.

## Target structure
```
FashXStudio/
├─ README.md  LICENSE  CONTRIBUTING.md  Makefile  pyproject.toml  alembic.ini  .env.example
├─ backend/fashx/   (api, application, domain, infrastructure, platform; frozen kept in place, router-gated by FASHX_ENABLE_FROZEN, tests marked frozen)
├─ workers/  ml/  mobile/  schemas/  database/  infra/  scripts/  tests/
└─ docs/  STATUS.md  product/  architecture/  adr/  design/  logs/  archive/
```

## Consequences
Smaller surface to secure and explain; frozen code stays recoverable; code moves happen later on branches, one move per commit, with the test suite as the safety net.
