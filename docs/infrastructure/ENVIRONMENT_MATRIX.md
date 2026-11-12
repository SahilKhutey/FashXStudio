# Environment Technical Specification Matrix

This matrix provides the side-by-side comparison of technical dimensions across all four FashXStudio environments.

| Dimension | 1. Local Workstation | 2. Shared Development | 3. Staging (RC) | 4. Production |
| :--- | :--- | :--- | :--- | :--- |
| **1. Identifiers** | `ENV=dev`<br>`APP_ENV=development` | `ENV=dev`<br>`APP_ENV=development` | `ENV=staging`<br>`APP_ENV=staging` | `ENV=prod`<br>`APP_ENV=production` |
| **2. Target Audience** | Core backend & mobile developers | Engineering team & CI bots | QA, pilots & founder qualification | Live end-shoppers & merchants |
| **3. Compute / Runtime** | Local host Python 3.12 / Docker | AWS ECS Fargate (Development Cluster) | AWS ECS Fargate (Staging Cluster) | AWS ECS Fargate (Production Cluster Multi-AZ) |
| **4. Database Engine** | SQLite (`aiosqlite`) or Local Docker PostgreSQL | Dedicated AWS RDS PostgreSQL (Single-AZ, `db.t4g.micro`) | Dedicated AWS RDS PostgreSQL (Multi-AZ, `db.t4g.small`) | Dedicated AWS RDS PostgreSQL (Multi-AZ, `db.r6g.large` with read replicas) |
| **5. Cache & Broker** | Local in-memory or Redis container (`redis://localhost:6379/0`) | Managed Redis (ElastiCache Single-node) | Managed Redis (ElastiCache Replication Group, TLS) | Managed Redis (ElastiCache Multi-AZ Cluster, TLS enabled) |
| **6. Object Storage** | Local filesystem (`storage_backend=local`, `./local_storage`) | Private S3 Bucket (`fashx-dev-media-private`) | Private S3 Bucket (`fashx-staging-media-private`) | Private S3 Bucket (`fashx-prod-media-private`) with SSE-KMS |
| **7. Identity & Auth** | Local symmetric JWT (`AUTH_MODE=local`, local secret) | Supabase Development Project (JWKS via HTTPS) | Supabase Staging Tenant (JWKS via HTTPS) | Supabase Production Project (Dedicated custom auth domain, JWKS via HTTPS) |
| **8. VTO Engine** | `TRYON_PROVIDER=mock` | `TRYON_PROVIDER=mock` or Dev FASHN Key | `TRYON_PROVIDER=fashn_api` (Staging budget-capped key) | `TRYON_PROVIDER=fashn_api` (Commercial production key, strict daily limit) |
| **9. CORS Origins** | `http://localhost:3000`, `http://localhost:8081` | `https://dev.fashxstudio.com`, `http://localhost:8081` | `https://staging.fashxstudio.com`, `https://pilot.fashxstudio.com` | Strict HTTPS: `https://fashxstudio.com`, `https://app.fashxstudio.com` |
| **10. Secret Management** | Local uncommitted `.env` file | AWS Secrets Manager (`/fashx/dev/*`) | AWS Secrets Manager (`/fashx/staging/*`) | AWS Secrets Manager (`/fashx/prod/*`) with automated IAM rotation |
| **11. Deployment Gate** | Local `make run` or manual command | Automated on merge to feature/development branch | Automated upon Release Candidate tag (`v*.*.*-rc*`) | Manual Founder Sign-Off (GitHub Release Gate with release checklist) |

---

## Technical Invariant Rules

1. **Storage Exclusivity**: No bucket may ever be accessed across environment lines. IAM policies on `fashx-prod-media-private` strictly reject any role assumed outside the Production ECS Task execution role.
2. **Database Role Segregation**: Development, Staging, and Production databases each have unique credentials and separate VPC security group ingress rules. Cross-VPC peering between Staging and Production is strictly prohibited.
3. **Identity Token Verification**: Production rejects any JWT token issued by staging or test issuers (`AUTH_ISSUER` mismatch check).
4. **VTO Provider Invariants**:
   - Setting `TRYON_PROVIDER=mock` in Production triggers immediate startup failure (`Settings._fail_fast()` rule I08).
   - Setting `TRYON_PROVIDER=fashn_selfhost` in Production triggers immediate startup failure because self-hosted inference is not yet implemented.
