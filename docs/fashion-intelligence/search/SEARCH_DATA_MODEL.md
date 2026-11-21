# Fashion Product Search Data Model

## 1. Searchable Unit & Entities
In FashXStudio, the atomic unit of shopper search is the **Merchant Product Listing** (`MerchantProduct` / `ProductSearchDocumentRecord`), paired with its **Active Eligible Offer** (`MerchantOffer`).

This design guarantees that:
1. Prices and currencies belong strictly to the merchant who sells the item.
2. Sizing availability evaluates the exact variant SKU inventory belonging to that merchant.
3. Brands and merchants are never conflated (e.g., Roadster is a brand, Myntra is a merchant).

---

## 2. Relational Search Schema

```mermaid
erDiagram
    merchant_products ||--o{ product_search_documents : "indexes"
    merchant_products ||--o{ product_text_embeddings : "embeds"
    merchant_products ||--o{ merchant_offers : "offers"
    merchant_offers ||--o{ merchant_offer_sizes : "stocks"
    search_sessions ||--o{ product_search_events : "tracks"

    product_search_documents {
        uuid id PK
        uuid merchant_product_id UK
        uuid product_id
        uuid merchant_id
        uuid brand_id
        uuid category_id
        string title
        text description
        tsvector search_document
        string taxonomy_version
        string enrichment_version
        string source_revision
        json indexed_attributes_json
        timestamp updated_at
    }

    product_text_embeddings {
        uuid id PK
        uuid merchant_product_id FK
        string model_id
        string model_version
        string text_revision_hash
        integer embedding_dimension
        vector512 embedding
        string status
        timestamp created_at
    }

    search_sessions {
        uuid id PK
        uuid user_id
        string session_token UK
        text query_text
        json applied_filters_json
        string sort_order
        json result_ids_json
        integer total_results
        timestamp created_at
        timestamp expires_at
    }

    product_search_events {
        uuid id PK
        uuid session_id FK
        uuid user_id
        string event_type
        text query
        string filter_key
        text filter_value
        uuid product_id
        uuid merchant_product_id
        integer rank_position
        json metadata_json
        timestamp created_at
    }

    search_synonyms {
        uuid id PK
        string term
        string synonym
        string category_scope
        boolean is_bidirectional
    }

    search_evaluation_runs {
        uuid id PK
        string evaluator_version
        integer dataset_size
        float precision_at_10
        float recall_at_10
        float mrr
        float ndcg_at_10
        float zero_result_rate
        integer hard_filter_violation_count
        integer takedown_violation_count
        json results_json
        timestamp created_at
    }
```

---

## 3. Search Document Definition
The normalized `search_document` field is constructed from verified and approved catalog attributes:
$$\text{Document} = \text{Title (Weight A)} \parallel \text{Brand (Weight A)} \parallel \text{Garment Type (Weight B)} \parallel \text{Color \& Occasion (Weight B)} \parallel \text{Description (Weight D)}$$

Only approved attributes from Phase 06.2 (`review_status in ('AUTO_ACCEPTED', 'APPROVED')`) with high confidence are incorporated into the search document. Unverified AI fabric inferences or speculative measurements are strictly excluded.
