# Hybrid Search Ranking & Candidate Merging

## 1. Candidate Fusion via Reciprocal Rank Fusion (RRF)
Hybrid search combines candidate rankings from three independent retrieval streams:
1. Keyword search (PostgreSQL full-text search)
2. Semantic search (Text-to-text / text-to-image vector similarity)
3. Visual search (Image-to-image nearest-neighbor similarity)

Because raw scores from BM25/ts_rank and cosine similarity have different distributions and scales, raw scores cannot be directly added. FashXStudio utilizes **Reciprocal Rank Fusion (RRF)**:
$$RRF(d) = \sum_{m \in M} w_m \cdot \frac{1}{k + \text{rank}_m(d)}$$
- $M$: Active retrieval modes (keyword, semantic, visual).
- $k$: Smoothing constant (default: $60$).
- $w_m$: Stream weight (default: $w_{\text{keyword}} = 1.0, w_{\text{semantic}} = 0.8, w_{\text{visual}} = 0.7$).

---

## 2. Business Boost Layer
Once initial fused scores are computed, domain-specific boosts are applied to products satisfying all hard filters:
- **Exact Title Match**: $+25\%$ score boost if the query terms match the title sequence.
- **Brand Match**: $+20\%$ score boost if the user query contains the product's brand name.
- **Verified In-Stock Status**: $+15\%$ score boost for confirmed in-stock offers over unverified stock.
- **Verified Attributes**: $+10\%$ boost if query attributes match verified Phase 06.2 attributes with confidence $\ge 0.95$.
