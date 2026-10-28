# FashXStudio — P1 Catalog and Recommendation Implementation

## Objective
Deliver a reliable personalized product feed based on valid catalog data and user preferences. Semantic similarity must only contribute when real, compatible embeddings are available.

## Implementation sequence
1. Audit the existing catalog models, enrichment pipeline and ranking tests.
2. Remove placeholder embedding generation from heuristic enrichment.
3. Make feed scoring independent of artificial embeddings.
4. Validate catalog records and deduplicate repeated imports.
5. Add a real embedding provider behind an explicit interface.
6. Persist and retrieve user style-quiz and feedback signals.
7. Generate version-compatible user and garment vectors.
8. Integrate semantic similarity with compatibility scoring.
9. Validate feed behavior through API and mobile integration tests.
10. Record evidence before claiming completion.

## Embedding contract
- Vector dimensions must match the configured model.
- Values must be finite numeric values.
- Zero or missing vectors must not be treated as semantic matches.
- Every embedding must have a model identifier and version.
- User and garment vectors must use compatible model versions.
- Recompute or invalidate cached vectors when the model changes.
- Never substitute a constant vector for a failed embedding request.

## Recommendation scoring
- The initial feed uses deterministic filtering and explicit compatibility scoring.
- Once the real embedding provider and user taste pipeline are connected, the scoring configuration may combine normalized compatibility, semantic similarity and other validated signals. Weights must be configurable, documented and tested against a baseline.
- Hard constraints—such as stock availability, explicit exclusions and budget limits—must not be overridden by semantic relevance.

## Acceptance criteria
- Catalog records validate against the canonical contract.
- Repeated ingestion does not create duplicate products or offers.
- Missing and malformed images are handled safely.
- No constant placeholder vectors are used as real semantic embeddings.
- The real embedder has explicit model/version metadata.
- User taste is derived from persisted preferences and eligible feedback.
- Different test personas can receive different rankings when their preferences differ.
- Hard exclusions are respected.
- Empty catalogs and empty matches produce valid API responses.
- Ranking is deterministic for fixed inputs and configuration.
- Mobile feed loading, pagination and save/feedback behavior are tested.
- Evaluation results and known limitations are documented.

## Evidence policy
A feature is complete only after tests have run successfully and the relevant CI run, commit SHA and remaining limitations are recorded.
A passing unit test is not proof of real-world recommendation quality. Human relevance ratings and product data quality must be evaluated separately.

## Exit condition
P1 is complete when the feed uses real catalog data, user preferences influence ranking, the embedding pipeline is versioned and tested, and the primary mobile feed journey is verified end to end.
