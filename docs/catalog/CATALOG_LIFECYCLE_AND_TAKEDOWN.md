# Catalog Lifecycle and Takedown Policy

## 1. Offer Lifecycle
```
ACTIVE
  |
  +----> OUT_OF_STOCK
  |
  +----> INACTIVE
  |
  +----> SOURCE_UNAVAILABLE
  |
  +----> SUSPENDED
```

## 2. Invariant: Takedown Immunity
- Ordinary sync operations can never reactivate or overwrite an offer or product with an active takedown (`REQUESTED`, `PROCESSING`, `COMPLETED`, `UNDER_REVIEW`).
- Takedowns take precedence over feed refreshes and snapshot reconciliations.
- Inactivity is strictly distinct from takedown deletion.
