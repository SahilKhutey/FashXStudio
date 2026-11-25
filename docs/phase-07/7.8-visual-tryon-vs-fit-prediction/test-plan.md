# Test Plan: Visual Try-On vs. Fit Prediction

> **Test inventory and verification matrix.**

## 1. Test Suite Categories
- **DISC (Disclosure Tests)**: `DISC-001` through `DISC-010` (API status responses, presentation policy, client override prevention).
- **SIZE (Size-Chart Tests)**: `SIZE-001` through `SIZE-014` (Basis validation, unit validation, duplicate size rejection, stale warnings).
- **FIT (Fit Recommendation Tests)**: `FIT-001` through `FIT-018` (Fail-closed missing data, rejection of VTO image evidence, conflicting measurements).
- **COPY (Claims & Content Policy Tests)**: `COPY-001` through `COPY-010` (Prohibited phrase detection, widget policy sanitization).
- **FDBK (Shopper Feedback Tests)**: `FDBK-001` through `FDBK-015` (Ownership verification, rate limiting, review status, privacy preservation).
- **INT (Integration & Regression Checks)**: Verifies that existing Phase 07.4–07.7 try-on lifecycles remain unbroken.
