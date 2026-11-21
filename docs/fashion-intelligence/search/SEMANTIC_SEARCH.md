# Semantic Text Search Specification

## 1. Overview
Semantic text search enables shoppers to find relevant fashion items using natural language, abstract occasions, or stylistic concepts (e.g., "minimalist linen shirt for a beach vacation", "festive ethnic wear for Diwali celebration").

---

## 2. Text Embedding Model & Alignment
- **Shared Multimodal Space**: Natural language queries are encoded into the exact same 512-dimensional vector space as Phase 06.3 image embeddings using the approved **OpenCLIP ViT-B/32** text encoder (`ViT-B-32-laion2b_s34b_b79k`).
- Vectors are L2 unit normalized ($\|v\|_2 = 1.0 \pm 10^{-4}$).
- Stored in `product_text_embeddings` with `Vector512` column in PostgreSQL + pgvector.

---

## 3. Product Semantic Representation
The text representation encoded for each product is deterministically synthesized from verified attributes:
```text
Title: Men's Regular Fit Cotton Navy Blue Shirt
Brand: Example Brand
Category: Apparel > Tops > Shirt
Color: Navy blue
Pattern: Solid
Fit: Regular fit
Occasion: Casual, Office
Silhouette: Straight
```
Speculative AI claims, unverified fabrics, or raw HTML markup are strictly excluded before encoding.

---

## 4. Query Execution
Cosine distance search using pgvector:
```sql
SELECT merchant_product_id, 1 - (embedding <=> :query_vector) AS similarity
FROM product_text_embeddings
WHERE model_id = :model_id AND status = 'READY'
ORDER BY embedding <=> :query_vector
LIMIT :limit;
```
Candidates retrieved from semantic search are merged with keyword and visual candidates in the hybrid ranking layer.
