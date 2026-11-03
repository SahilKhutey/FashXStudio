# RC-03 — Feedback & Personalization Learning

## Continuous Taste Learning Loop

The recommendation engine adapts the user's discovery feed based on active and passive feedback:

1. **Feed Signals**: User interactions (`like`, `hide`, `not_interested`) posted via `/api/v1/feed/signals`.
2. **Wardrobe Saves**: Garments saved to virtual closet serve as positive preference signals.
3. **Style Quiz**: Initial archetype selections initialize the cold-start taste vector.
4. **Taste Vector Synthesis**: Blends style archetypes with recent interaction embeddings using time-decayed exponential weighting.

## Fallback Embedding Resilience
When a catalog garment has not yet completed asynchronous neural embedding extraction (e.g. enriched via heuristic enricher), `generate_feed.py` falls back to deterministic text embeddings via `fallback_text_embedding` rather than silently dropping positive signals.

This mechanism was verified in `tests/unit/test_personalization_ranking.py::test_feed_signals_and_wardrobe_saves_steer_feed`, proving that user interactions immediately prioritize matching style archetypes over generic alternatives.
