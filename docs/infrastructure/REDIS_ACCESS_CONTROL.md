# Redis Access Control and Authentication Policy

> **Security policy. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Authentication Model

AWS ElastiCache for Redis supports two authentication patterns:
1. **Redis AUTH Token**: Secret password provided during connection handshake (`AUTH <token>`).
2. **IAM Authentication for Redis**: Role-based token exchange supported in Redis 7+.

FashXStudio adopts **Redis AUTH Token stored in AWS Secrets Manager** for broad client compatibility across Python `redis-py`, Kombu, and Celery worker transports.

---

## 2. Secrets Management

Auth tokens are generated automatically via Terraform using cryptographic random generation (32 alphanumeric characters) and stored in AWS Secrets Manager:

- **Staging Token ARN**: `/fashx/staging/redis/auth_token`
- **Production Token ARN**: `/fashx/prod/redis/auth_token`

### Secret Ingestion Protocol:
1. ECS / EKS application tasks fetch the AUTH token at container startup via AWS Systems Manager Parameter Store or Secrets Manager IAM integration.
2. The runtime environment variable `REDIS_URL` is assembled securely:
   ```text
   rediss://:{AUTH_TOKEN}@fashx-redis-prod.xxxxxx.clustercfg.aps1.cache.amazonaws.com:6379/0
   ```
3. Tokens are never committed to version control, logged in application traces, or exposed in error messages.

---

## 3. Network-Level Access Restriction

In addition to AUTH tokens, all Redis endpoints reside exclusively in private subnets with no public IP allocation:
- **Direct Internet Ingress**: Disallowed (0.0.0.0/0 denied).
- **VPC Peering / Transit Gateway Ingress**: Restricted to authorized backend subnets.
- **Port Ingress**: Port 6379 allowed solely from security groups attached to backend FastAPI pods and Celery worker instances (`fashx-app-sg`).
