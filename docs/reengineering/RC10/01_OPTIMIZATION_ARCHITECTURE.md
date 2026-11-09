# RC10: Optimization Architecture

## 1. System Context
FashXStudio connects mobile clients with a modular backend API, persistent PostgreSQL storage (with pgvector for visual and semantic embeddings), Redis job queues, and external AI try-on providers.

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        Mobile["Expo React Native (iOS / Android)"]
    end

    subgraph Gateway ["API & Security Gateway"]
        FastAPI["FastAPI App (ASGI)"]
        Auth["JWKS / Auth Guard"]
        ReleaseGuard["ReleaseConfig Gatekeeper"]
    end

    subgraph CoreServices ["Core Domain Services"]
        CatSvc["Catalog Service & Ingestion"]
        RecSvc["Recommendation Ranker (512-dim)"]
        VTOSvc["VTO Orchestrator"]
        WardrobeSvc["Wardrobe & Buy-Click Handoff"]
    end

    subgraph DataStorage ["Persistence & Storage"]
        PG[("PostgreSQL + pgvector")]
        RedisQueue[("Redis Queue / Streams")]
        S3Bucket[("Private S3 Storage")]
    end

    subgraph External ["External Providers"]
        VTOProvider["FASHN API / Real Try-On"]
        RetailerLink["Retailer Web Handoff"]
    end

    Mobile -->|HTTPS / Bearer JWT| FastAPI
    FastAPI --> Auth
    FastAPI --> ReleaseGuard
    FastAPI --> CatSvc
    FastAPI --> RecSvc
    FastAPI --> VTOSvc
    FastAPI --> WardrobeSvc

    CatSvc --> PG
    RecSvc --> PG
    VTOSvc --> RedisQueue
    VTOSvc --> S3Bucket
    WardrobeSvc --> PG

    RedisQueue --> VTOProvider
    WardrobeSvc --> RetailerLink
```

## 2. Invariants & Guardrails
1. **Zero Fake Data as Pilot Evidence**: Simulated or test datasets must never be marked as real pilot evidence.
2. **Fail-Closed Release Gates**: All 9 beta gates (`B1` through `B9`) must evaluate to True for release authorization (`GO`); any missing or false gate holds release (`HOLD`).
3. **Environment Security**: Production configurations reject mock VTO providers, local SQLite storage, wildcard CORS, and debug modes.
4. **Idempotency & Deduplication**: Purchase clicks, wardrobe additions, and try-on requests enforce strict idempotency keys and prevent duplicate submissions.
