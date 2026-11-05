# RC07 — Implementation Task List

| Task ID | Task Description | Scope Area | Status | Evidence |
|---|---|---|---|---|
| T07.01 | Branch creation & baseline verification from `main` (`db2609e`) | Git / Repo | 🟢 DONE | Branch `recovery/rc07-catalog-personalization` |
| T07.02 | Heuristic enricher correction: remove `FakeEmbedder`, pure attributes | Backend / Catalog | 🟢 DONE | `tests/unit/test_rc07_enrichment.py` (3 passed) |
| T07.03 | Image byte, pixel, format, and SSRF permission validation | Backend / Images | 🟢 DONE | `tests/unit/test_rc07_image_validation.py` (5 passed) |
| T07.04 | Multimodal embedder protocol: add `model_version: str` | Backend / Embeddings | 🟢 DONE | `ports.py`, `fake.py`, `marqo_fashionclip.py` |
| T07.05 | Implement `EmbeddingService` for vector validation and batching | Backend / Embeddings | 🟢 DONE | `tests/unit/test_rc07_embedding_service.py` (4 passed) |
| T07.06 | Model versioning and environment safety guards | Backend / Embeddings | 🟢 DONE | `tests/unit/test_rc07_embedding_versioning.py` (4 passed) |
| T07.07 | Update batch embedding script with `<model_id>:<model_version>` | Scripts / Catalog | 🟢 DONE | `tests/integration/test_rc07_embedding_persistence.py` (1 passed) |
| T07.08 | Personalization taste vector engine with 14-day exponential decay | Backend / Discovery | 🟢 DONE | `tests/unit/test_rc07_taste_vector.py` (5 passed) |
| T07.09 | Feedback collection pipeline with strict JWT user ownership | Backend / Feed | 🟢 DONE | `tests/integration/test_rc07_feedback_pipeline.py` (3 passed) |
| T07.10 | Multi-attribute scoring engine with dynamic reweighting | Backend / Discovery | 🟢 DONE | `tests/unit/test_rc07_scoring.py` (4 passed) |
| T07.11 | Grounded reason chips & stylist explanation generation | Backend / Discovery | 🟢 DONE | `tests/unit/test_rc07_explanations.py` (2 passed) |
| T07.12 | Hard eligibility gating & feed generation integration | Backend / Recommendation | 🟢 DONE | `tests/integration/test_rc07_personalized_feed.py` (1 passed) |
| T07.13 | Cross-user recommendation feed and signal isolation | Backend / Security | 🟢 DONE | `tests/integration/test_rc07_user_isolation.py` (1 passed) |
| T07.14 | Recommendation API contract schema conformance | Contracts | 🟢 DONE | `tests/contracts/test_rc07_recommendation_contract.py` (1 passed) |
| T07.15 | Evaluation metrics suite: Precision@K, Recall@K, NDCG@K | Evaluation | 🟢 DONE | `tests/evaluation/test_rc07_ranking_metrics.py` (1 passed) |
| T07.16 | Multi-persona relevance divergence evaluation | Evaluation | 🟢 DONE | `tests/evaluation/test_rc07_persona_relevance.py` (1 passed) |
| T07.17 | Mobile TypeScript compilation & Jest unit test verification | Mobile / Frontend | 🟢 DONE | `tsc` (0 errors), `jest` (21 suites, 152 tests passed) |
| T07.18 | Complete 17-document RC07 documentation package | Docs | 🟢 DONE | `docs/reengineering/RC07/` |
