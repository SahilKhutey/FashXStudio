# RC08 — Deployment Architecture

## 1. Architectural Strategy: Modular Monolith with Asynchronous Workers
FashX preserves a clean, modular monolith backend architecture rather than decomposing into unneeded microservices. Heavy workloads (catalog scraping, ML enrichment, virtual try-on, and image deletion) run asynchronously via Celery worker processes backed by Redis.

## 2. 3-Tier Infrastructure Model

```mermaid
flowchart TD
    subgraph Presentation & Client Tier
        MobileApp[React Native Mobile App: Android / iOS]
    end

    subgraph Edge & Ingress Tier
        EdgeGateway[Cloudflare / AWS CloudFront]
        ALB[Application Load Balancer: TLS 1.3]
        EdgeGateway --> ALB
    end

    subgraph Application Tier
        FastAPI[FastAPI Application Service: ECS Fargate / App Platform]
        CeleryWorkers[Celery Worker Cluster: Concurrency=3]
        ALB --> FastAPI
    end

    subgraph Data & Storage Tier
        Postgres[(Managed PostgreSQL 16 + pgvector)]
        Redis[(Managed Redis 7: Persistence enabled)]
        S3[(Private Object Storage: AWS S3 / Cloudflare R2)]
        FastAPI --> Postgres
        FastAPI --> Redis
        FastAPI --> S3
        CeleryWorkers --> Postgres
        CeleryWorkers --> Redis
        CeleryWorkers --> S3
    end

    subgraph Identity & AI Tier
        Supabase[Supabase Identity: JWKS Endpoint]
        FashnAI[Fashn.ai VTO Inference Provider]
        FastAPI -.->|Token Verification| Supabase
        CeleryWorkers -.->|Async Try-On Task| FashnAI
    end

    MobileApp -->|HTTPS / API Requests| EdgeGateway
```

## 3. Network Isolation & Security Zones
- **Public Zone**: Application Load Balancer / Edge CDN terminating public TLS certificates.
- **Private App Zone**: FastAPI and Celery worker containers located in private subnets with NAT egress only.
- **Data Zone**: PostgreSQL and Redis instances bound exclusively to private VPC subnets with no public IPv4 addresses.
- **Object Storage Access**: Direct IAM role attachment or restricted S3 access credentials. All buckets enforce `BlockPublicAccess=true`.
