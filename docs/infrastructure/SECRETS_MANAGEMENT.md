# Secrets Management and Credential Security

## 1. Zero Hardcoded Secrets Invariant

No cryptographic secret, database password, cloud service key, or third-party API token may ever be committed to git, written to application configuration files, or embedded into container images.

Enforcement mechanisms:
- **Pre-commit scanning**: Local git hooks prevent staging commits containing credentials.
- **CI Gitleaks / TruffleHog validation**: Every pull request and push is scanned automatically in CI. Any detected secret halts the build immediately.
- **Pydantic `SecretStr` typing**: Sensitive attributes in `backend/fashx/core/settings.py` (`auth_jwt_secret`, `database_url`, `fashn_api_key`, `supabase_secret_key`, `s3_secret_access_key`) are declared as Pydantic `SecretStr`. Standard logging, string representations, and error serializations automatically mask the values as `**********`.

---

## 2. Secrets Hierarchy and AWS Secrets Manager Namespaces

In hosted environments (Staging and Production), secrets are provisioned in AWS Secrets Manager using hierarchical path namespaces:

```text
/fashx/
├── dev/
│   ├── database_credentials
│   ├── redis_auth
│   ├── fashn_api_key
│   └── sentry_dsn
├── staging/
│   ├── database_credentials
│   ├── redis_auth
│   ├── supabase_service_role_key
│   ├── fashn_api_key
│   └── sentry_dsn
└── prod/
    ├── database_credentials
    ├── redis_auth
    ├── supabase_service_role_key
    ├── fashn_api_key
    └── sentry_dsn
```

### Namespace Isolation Rules
1. The Production ECS Task Execution Role has IAM permissions scoped exclusively to `/fashx/prod/*`.
2. Staging compute tasks cannot read `/fashx/prod/*`.
3. Development tasks cannot read `/fashx/staging/*` or `/fashx/prod/*`.

---

## 3. Secret Inventory and Usage

| Secret Key Identifier | Pydantic Setting | Invariant & Validation | Rotation Window |
| :--- | :--- | :--- | :--- |
| `DATABASE_PASSWORD` | `database_url` | Injected into asyncpg connection string | 90 days (Automated via RDS Lambda) |
| `REDIS_PASSWORD` | `redis_url` | Auth token for ElastiCache Redis cluster | 90 days |
| `FASHN_API_KEY` | `fashn_api_key` | Commercial VTO provider inference authorization | 180 days or upon credential exposure |
| `SUPABASE_SERVICE_KEY`| `supabase_secret_key`| Admin API key for user profile sync | 180 days |
| `SENTRY_DSN` | `sentry_dsn` | Application crash reporting ingest key | Indefinite (rotated on abuse) |

---

## 4. Rotation Procedures

### 4.1 Scheduled 90-Day Rotation
1. **Database Credentials**: Managed PostgreSQL passwords rotate via AWS Secrets Manager RDS rotation lambda. The rotation lambda creates a shadow user, tests connectivity, updates the secret ARN, and gracefully retires the previous password after 24 hours.
2. **Third-Party API Keys**: Dual-key rotation where the new key is generated in the vendor console, added to Secrets Manager, verified via staging smoke tests, and the old key is subsequently revoked.

### 4.2 Emergency Revocation Runbook
In the event of suspected credential compromise:
1. **Immediate Revocation**: Invalidate the compromised API token or database user at the provider console or RDS instance.
2. **Generate Replacement**: Generate and store a new secret in `/fashx/<env>/...`.
3. **Task Force Update**: Trigger an ECS service rolling update to pull fresh secret values:
   ```bash
   aws ecs update-service --cluster fashx-production --service fashx-api --force-new-deployment
   ```
4. **Audit Log Inspection**: Review CloudTrail and VPC Flow Logs for unauthorized access during the exposure window.
