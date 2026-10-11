# Secrets Inventory & Rotation Runbook

## Overview
All production secrets are stored in AWS Secrets Manager and referenced dynamically by ECS Task Definitions. No long-lived secrets reside in source repositories, container images, or shared `.env` files.

## Secrets Inventory

| Secret Name | Location / Key | Owner | Consumption Point | Rotation Cadence |
| :--- | :--- | :--- | :--- | :--- |
| **Database Password** | `/fashx/prod/DATABASE_URL` | Lead Engineer | RDS PostgreSQL, ECS API & Workers | 90 days |
| **Redis Auth Token** | `/fashx/prod/REDIS_URL` | Lead Engineer | ElastiCache Redis, Celery Broker | 90 days |
| **Supabase Secret Key** | `/fashx/prod/SUPABASE_SECRET_KEY` | Lead Engineer | Account erasure worker (Admin API) | 180 days |
| **FASHN Try-On API Key** | `/fashx/prod/FASHN_API_KEY` | Lead Engineer | Try-on worker adapter | 90 days |
| **Anthropic VLM API Key** | `/fashx/prod/ANTHROPIC_API_KEY` | Lead Engineer | Catalog enrichment worker | 90 days |
| **Internal Service Token**| `/fashx/prod/INTERNAL_SERVICE_TOKEN`| Lead Engineer | System-to-system health & sync routes | 180 days |

## Step-by-Step Rotation Procedures

### 1. Rotating Supabase Secret Key
1. Navigate to Supabase Dashboard → Project Settings → API.
2. Generate a new `service_role` (secret) key.
3. Update secret in AWS Secrets Manager:
   ```bash
   aws secretsmanager update-secret --secret-id "/fashx/prod/SUPABASE_SECRET_KEY" --secret-string "<NEW_KEY>"
   ```
4. Trigger rolling ECS deployment:
   ```bash
   aws ecs update-service --cluster fashx-prod --service fashx-worker --force-new-deployment
   ```
5. Verify test erasure execution on staging before revoking old key in Supabase.

### 2. Rotating FASHN Try-On API Key
1. Generate new key on FASHN Developer Console.
2. Update secret in AWS Secrets Manager:
   ```bash
   aws secretsmanager update-secret --secret-id "/fashx/prod/FASHN_API_KEY" --secret-string "<NEW_KEY>"
   ```
3. Restart worker tasks; submit single synthetic try-on job to verify.
4. Revoke previous key in vendor portal.

### 3. Rotating Database Credentials (RDS)
1. In RDS Console, configure a secondary master user or update user password with `Apply Immediately`.
2. Update connection string in Secrets Manager.
3. Restart API and Worker services sequentially.
