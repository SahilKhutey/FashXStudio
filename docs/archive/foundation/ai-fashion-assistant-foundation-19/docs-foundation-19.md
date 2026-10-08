# AI Fashion Assistant — Foundation 19

## Pre-Final Unit Tests, Verification & Validation

Foundation 19 is the pre-final quality gate for the MVP build. It does not add a new external vendor or a production analytics warehouse. It consolidates the complete MVP journey into explicit, testable state/gate contracts and establishes the release verification procedure.

### MVP journey contract

```text
Profile incomplete
      ↓
Profile ready
      ↓
Try-on photo ready
      ↓
Garment selected
      ↓
Try-on running
      ↓
Try-on completed
      ↓
Decision
      ↓
Validation captured
```

The journey model is deliberately pure and does not read the database or call external services. Runtime APIs remain the source of truth; these contracts are the pre-final acceptance layer used by tests and future orchestration.

### Pre-final test categories

- Domain/unit: journey state derivation and gates.
- Contract: schema strictness and API route presence.
- Existing subsystem suites: profile, media, catalog, feed, commerce, try-on, feedback and analytics.
- Static integrity: Python compilation and migration SQL generation.

### Validation scenarios

1. New user cannot start Try-On without a complete profile.
2. A ready profile cannot start Try-On without an accepted reference photo.
3. A ready photo cannot start Try-On without a selected garment.
4. A valid profile + photo + garment can enter Try-On.
5. Validation feedback cannot be captured before a completed Try-On result.
6. A completed Try-On can enter validation.
7. Terminal validation state remains terminal even when earlier flags remain true.
8. Public MVP routes remain registered after all feature modules are mounted.
9. Shared journey contracts reject undeclared fields.
10. Full test suite and Alembic migration chain remain green.

### Release-gate commands

```bash
./scripts/verify_foundation_19.sh
```

The script runs compilation, the complete pytest suite, and offline Alembic SQL generation.

### Validation boundary

Foundation 19 verifies engineering correctness and MVP-flow integrity. It does **not** claim that the commercial VTO model is licensed, that real GPU execution is available in this environment, or that purchase conversion has been causally validated. Those remain external/runtime/product-validation gates.
