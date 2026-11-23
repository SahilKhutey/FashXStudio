# Search Subsystem Implementation & Operations Runbook

## 1. Overview
Operational guide for maintaining, monitoring, and debugging the FashXStudio unified search engine.

---

## 2. Configuration & Environment Variables
```bash
# Search settings
SEARCH_DEFAULT_PAGE_SIZE=20
SEARCH_MAX_PAGE_SIZE=50
SEARCH_SESSION_TTL_MINUTES=15
SEARCH_DEFAULT_CURRENCY="INR"

# Vector and embedding settings
SEARCH_TEXT_MODEL_ID="openclip_vit_b32"
SEARCH_TEXT_MODEL_VERSION="v1"
SEARCH_EMBEDDING_DIM=512

# RRF Parameters
SEARCH_RRF_K=60
SEARCH_KEYWORD_WEIGHT=1.0
SEARCH_SEMANTIC_WEIGHT=0.8
SEARCH_VISUAL_WEIGHT=0.7
```

---

## 3. Database Maintenance & Index Rebuilding
```sql
-- Rebuild search document index
REINDEX INDEX product_search_document_gin_idx;

-- Vacuum analyze search tables
VACUUM ANALYZE product_search_documents;
VACUUM ANALYZE product_text_embeddings;
VACUUM ANALYZE search_sessions;
```

---

## 4. Operational Monitoring
- **Query Latency**: Alert if p95 exceeds 50ms for keyword search or 100ms for hybrid search.
- **Zero-Result Rate**: Alert if zero-result queries exceed 15% over a 1-hour rolling window.
- **Takedown Exclusions**: Ensure daily zero-tolerance verification that no items in `catalog_image_takedowns` appear in search indices.
