# Foundation 1 — Shared Contracts and Data Model

Foundation 1 is the first production-shaped data/contract layer.

## Locked boundaries

- Pydantic schemas are the shared wire/domain contract.
- SQLAlchemy models are persistence concerns and are not reused as API models.
- Canonical garment identity is separate from merchant listings/offers.
- Image hashes belong to image assets, not the garment aggregate.
- Fit observations are not converted directly into physical garment measurements.
- Try-on idempotency is separate from try-on artifact identity.
- User media is represented by object-store metadata only.
- Visual try-on feedback is separate from physical fit feedback.
- Domain events are historical facts, not domain state ownership.

## Migration chain

```text
0001_foundation
      ↓
0002_domain_foundation
```

## MVP compatibility

The schema is production-shaped but the MVP can implement only the profile, curated catalog, try-on, wardrobe, commerce, feedback, and event subsets it needs. Future V1 workers and recommendation services can reuse the same contracts without a data rewrite.
