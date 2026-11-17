# Deployment Secrets and Confidentiality Policy

## 1. Principles of Secret Handling

1. **Zero Hardcoded Secrets**: No API keys, passwords, database credentials, or tokens may exist in Git repositories, Docker images, or documentation.
2. **Runtime Injection via AWS Secrets Manager**: Application tasks in ECS Fargate receive sensitive credentials as container environment variables dynamically loaded from AWS Secrets Manager ARNs at task startup.
3. **No Secrets in Process Arguments**: Secrets must never be passed via CLI arguments (e.g. `--token <SECRET>`). Environment variables or secure file mounts must be used.
4. **Log Sanitization and Scrubbing**: Application and script loggers must filter sensitive tokens, authorization headers, and user identifiers.

## 2. Secrets Inventory by Environment

| Secret Identifier | Environment | Managed By | Purpose |
| :--- | :--- | :--- | :--- |
| `fashx/<env>/postgres/database-url` | dev, staging, prod | AWS Secrets Manager | Application runtime PostgreSQL connection URI with least-privilege role (`fashx_app`). |
| `fashx/<env>/postgres/migration-url` | dev, staging, prod | AWS Secrets Manager | Schema migration PostgreSQL connection URI with DDL owner role (`fashx_owner`). |
| `fashx/<env>/redis/url` | dev, staging, prod | AWS Secrets Manager | Redis / Valkey broker connection URI including TLS flag and AUTH token. |
| `SMOKE_TEST_TOKEN` | staging, prod | GitHub Actions Secret | Synthetic test bearer token for non-destructive smoke verification. |

## 3. Masking and Detection Controls

- **Gitleaks Pre-Commit and CI**: The `gitleaks/gitleaks-action@v3` step runs on all pull requests, analyzing git diffs against comprehensive credential signatures.
- **Python Smoke Test Sanitization**: `scripts/release/smoke.py` reads tokens from `SMOKE_TEST_TOKEN` and replaces user IDs with sanitized indicators (`[PASS] User identity confirmed (identifier sanitized)`).
- **GitHub Actions Automatic Masking**: Any secret registered in GitHub Secrets is automatically scrubbed by the runner if printed, displaying as `***`.
