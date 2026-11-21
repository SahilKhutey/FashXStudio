# ADR 0006: Selection of Fashion Image Embedding Model

## Status
Accepted

## Date
2026-11-21

## Context
FashXStudio requires a high-quality, reproducible, and permission-aware image embedding subsystem to support:
1. Visual product similarity search (finding products visually matching an input photo or garment).
2. Similar-product recommendations and style discovery.
3. Catalog deduplication and near-duplicate image detection.
4. Multimodal retrieval (aligning natural language fashion queries with garment imagery).

The model must:
- Generate fixed-dimensional numerical representations (512 dimensions) of fashion product imagery.
- Support cosine distance retrieval with consistent L2 normalization.
- Possess verified commercial-use and self-hosted deployment licenses.
- Operate reliably with deterministic preprocessing and versioned checkpoints.

## Evaluated Candidates

1. **OpenCLIP (ViT-B/32, pretrained on LAION-2B / DataComp-1B)**:
   - **Architecture**: Vision Transformer Base (ViT-B/32), 512-dimensional embedding space.
   - **Strengths**: Shared image-text embedding space; open-source weights; excellent cross-modal alignment; robust feature representation across diverse apparel categories.
   - **Licensing**: MIT / Apache 2.0 (unrestricted commercial use, self-hosted deployment permitted).
   - **Decision**: Selected as the primary production baseline.

2. **DINOv2 (ViT-B/14, Meta AI)**:
   - **Architecture**: Self-supervised Vision Transformer, 768-dimensional space.
   - **Strengths**: Dense self-supervised visual features, exceptional silhouette and shape discrimination.
   - **Limitations**: No native text embedding space; standard base weights are Apache 2.0, but specialized checkpoints have non-commercial restrictions; 768-dim requires separate vector partitioning.
   - **Decision**: Approved as secondary candidate for visual-only comparison benchmarks.

3. **SigLIP (Google Research)**:
   - **Strengths**: Sigmoid loss pretraining, strong zero-shot classification.
   - **Limitations**: Higher inference compute overhead for baseline catalog scale.
   - **Decision**: Deferred for Phase 06.4 evaluation.

## Decision
FashXStudio adopts **OpenCLIP ViT-B/32 (512 dimensions, L2 normalized)** as the primary image embedding model for Phase 06.3.

All model calls are encapsulated behind the `ImageEmbeddingAdapter` protocol to ensure zero vendor lock-in. Embeddings are stored in PostgreSQL with pgvector, indexed using HNSW on cosine similarity.

## Consequences
- **Positive**: Shared 512-dimensional text-image space enables both visual search and future natural language image retrieval.
- **Positive**: Strict licensing verification ensures uninhibited commercial deployment.
- **Negative**: Model upgrades require dual-version coexistence and blue/green vector migration (`EMB-019`).
- **Boundary**: Embeddings capture visual appearance only; they do not establish fabric composition, size availability, or interchangeability.
