# RC-03 — System Integration Architecture

## Architectural Topology

The FashXStudio system architecture integrates the mobile client, API gateway, persistence engines, and external merchant partners:

```mermaid
flowchart TB
    subgraph MobileApp ["Mobile Frontend (Expo / React Native)"]
        UI["Navigation & Feature Tabs<br>(Discover, Explore, Looks, Closet)"]
        QS["QueryClient State & Cache<br>(User-Scoped Key Registry)"]
        AuthStore["Zustand AuthStore<br>(Token & Session Lifecycle)"]
        RedirectVal["Safe Redirect Validator<br>(Strict HTTPS & Host Checking)"]
    end

    subgraph BackendGateway ["API Gateway & Core (FastAPI)"]
        MW["Middleware<br>(Trace ID, Request ID, CORS)"]
        Security["JWT Security & Auth Gate<br>(Bearer Token / Principal)"]
        HealthRouter["Health Probes<br>(/healthz/live, /healthz/ready)"]
        FeedRouter["Discovery Feed API<br>(/api/v1/feed)"]
        CommerceRouter["Commerce & Wardrobe API<br>(/api/v1/commerce, /api/v1/wardrobe)"]
        TryOnRouter["Virtual Try-On API<br>(/api/v1/tryon)"]
    end

    subgraph DataStorage ["Persistence & Storage Layer"]
        DB[("PostgreSQL / SQLite<br>Relational Database")]
        Storage[("Local / S3 Compatible<br>Object Storage")]
    end

    subgraph External ["External Ecosystem"]
        Retailers["Partner Retailer Sites<br>(Affiliate Destination)"]
    end

    UI --> QS
    UI --> AuthStore
    UI --> RedirectVal
    QS --> MW
    AuthStore --> MW
    MW --> Security
    Security --> HealthRouter
    Security --> FeedRouter
    Security --> CommerceRouter
    Security --> TryOnRouter
    FeedRouter --> DB
    CommerceRouter --> DB
    TryOnRouter --> DB
    TryOnRouter --> Storage
    RedirectVal -.-> Retailers
```

## Data Flow Sequences

### 1. Authenticated Discovery & Feed
1. Mobile fetches `/api/v1/me` with Bearer JWT token to retrieve authenticated principal and onboarding status.
2. Mobile queries `/api/v1/feed` with user query key `["feed", userId]`.
3. Backend filters candidates through deterministic filters (budget, excluded items), scores relevance against user taste vector and body compatibility, applies MMR diversification, generates natural language stylist explanations, and returns items.

### 2. Outbound Commerce Attribution (Rule I12)
1. User taps "Shop at retailer" or "Buy".
2. Mobile posts to `/api/v1/commerce/buy-clicks` with `garment_id` and optional `offer_id`.
3. Backend verifies offer in-stock status and destination URL HTTPS requirement, generates attribution `tracking_id`, stores click record, and appends UTM parameters.
4. Mobile validates redirect URL with `isSafeRetailerRedirect` before launching `WebBrowser.openBrowserAsync`.
