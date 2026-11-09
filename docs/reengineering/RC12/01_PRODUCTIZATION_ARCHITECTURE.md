# RC12: Productization Architecture

## 1. System Topology
RC12 preserves the modular monolith architecture while introducing strict server-side capability policy enforcement and operational health monitors.

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        Mobile["Expo App (iOS / Android)"]
    end

    subgraph Policy ["Release Policy & Gateway"]
        Gateway["FastAPI Gateway"]
        ReleasePolicy["fashx.core.release_policy<br/>(Deterministic Rollout, Kill Switches)"]
        Auth["JWKS / Identity Guard"]
    end

    subgraph OperationalMonitors ["Operations & Health Services"]
        CatHealth["scripts.rc12.catalog_health<br/>(Freshness, Permissions, Outages)"]
        VTOCost["scripts.rc12.vto_cost_report<br/>(Quotas, Mode Labels, Spend Warning)"]
        BetaGates["scripts.rc12.beta_gates<br/>(G1–G6 Evaluator)"]
    end

    subgraph CoreServices ["Core Domain Modules"]
        Catalog["Catalog Ingestion & Normalizer"]
        Ranker["Personalization Ranker (512-dim)"]
        TryOn["VTO Job Orchestrator"]
        Commerce["Closet & Retailer Redirects"]
    end

    subgraph Infrastructure ["Persistence & External"]
        PG[("PostgreSQL + pgvector")]
        RedisQueue[("Redis Queue")]
        S3Storage[("Private S3 Object Storage")]
        VendorAPI["Verified VTO Vendor API"]
        Retailer["Partner Merchant Web Store"]
    end

    Mobile -->|HTTPS / Bearer| Gateway
    Gateway --> Auth
    Gateway --> ReleasePolicy
    ReleasePolicy --> Catalog
    ReleasePolicy --> Ranker
    ReleasePolicy --> TryOn
    ReleasePolicy --> Commerce

    Catalog --> PG
    Ranker --> PG
    TryOn --> RedisQueue
    TryOn --> S3Storage
    TryOn --> VendorAPI
    Commerce --> Retailer

    CatHealth -.-> Catalog
    VTOCost -.-> TryOn
    BetaGates -.-> Gateway
```

## 2. Invariants
- **Deterministic Cohorting**: Users are mapped to rollout percentages using `sha256(salt:capability:user_id) % 100`.
- **Fail-Closed Capabilities**: Unconfigured capabilities or capabilities requiring unverified providers fail closed.
- **Retailer Redirection**: Handoffs validate destination domains against an approved partner allowlist.
