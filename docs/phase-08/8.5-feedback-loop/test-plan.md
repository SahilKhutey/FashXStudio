# Phase 08.5 Test Plan

- `tests/unit/feedback/test_feedback_loop.py`: Event deduplication & payload-hash conflict, single-state reaction & saved projections, cross-shopper isolation, consent withdrawal blocking ingestion/processing/ranking projections, server-only VTO/purchase event enforcement, VTO failure isolation from product reactions, UTC timestamp skew rejection & half-life decay, and bias/CTR monitoring metrics.
- `mobile/__tests__/feedback_loop.test.tsx`: `ProductReactionControl`, `SaveProductButton`, `setProductReaction`, `saveProduct`, and `submitFeedbackEvent`.
