# GitHub Actions Configuration Specification

## 1. Required Repository Variables (`vars`)

GitHub Actions workflows consume configuration settings through GitHub Repository Variables (`Settings -> Secrets and variables -> Actions -> Variables`).

| Variable Name | Environment Scope | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `AWS_BUILD_ROLE_ARN` | Repository / Global | `arn:aws:iam::123456789012:role/fashx-gh-actions-build` | IAM role assumed via OIDC to build and push container images to ECR. |
| `AWS_DEPLOY_ROLE_ARN` | Repository / Global | `arn:aws:iam::123456789012:role/fashx-gh-actions-deploy` | IAM role assumed via OIDC to register task definitions and update ECS services. |
| `AWS_REGION` | Global | `ap-south-1` | Target AWS region (Mumbai). |
| `ECS_CLUSTER_STAGING` | staging | `fashx-staging` | ECS cluster name for staging workloads. |
| `ECS_CLUSTER_PROD` | production | `fashx-prod` | ECS cluster name for production workloads. |
| `ECS_API_SERVICE_STAGING` | staging | `fashx-staging-api` | ECS service name for staging FastAPI application. |
| `ECS_API_SERVICE_PROD` | production | `fashx-prod-api` | ECS service name for production FastAPI application. |
| `ECS_TRYON_SERVICE_STAGING`| staging | `fashx-staging-tryon` | ECS service name for staging Celery Try-On worker. |
| `ECS_TRYON_SERVICE_PROD` | production | `fashx-prod-tryon` | ECS service name for production Celery Try-On worker. |
| `ECS_INGEST_SERVICE_STAGING`| staging | `fashx-staging-ingest` | ECS service name for staging Celery Ingestion worker. |
| `ECS_INGEST_SERVICE_PROD` | production | `fashx-prod-ingest` | ECS service name for production Celery Ingestion worker. |
| `ECS_BEAT_SERVICE_STAGING` | staging | `fashx-staging-beat` | ECS service name for staging Celery Beat scheduler. |
| `ECS_BEAT_SERVICE_PROD` | production | `fashx-prod-beat` | ECS service name for production Celery Beat scheduler. |
| `ECS_SUBNETS_STAGING` | staging | `subnet-01a,subnet-01b` | Comma-separated private subnet IDs for staging migration tasks. |
| `ECS_SUBNETS_PROD` | production | `subnet-02a,subnet-02b` | Comma-separated private subnet IDs for production migration tasks. |
| `ECS_SECURITY_GROUPS_STAGING` | staging | `sg-01a2b3c4d5e6f7g8h` | Security group allowing migration task egress to RDS. |
| `ECS_SECURITY_GROUPS_PROD` | production | `sg-09i8h7g6f5e4d3c2b` | Security group allowing production migration task egress to RDS. |
| `API_BASE_STAGING` | staging | `https://staging-api.fashxstudio.com` | Base URL used by smoke tests for staging verification. |
| `API_BASE_PROD` | production | `https://api.fashxstudio.com` | Base URL used by smoke tests for production verification. |

## 2. Required Repository Secrets (`secrets`)

GitHub Actions workflows consume sensitive values strictly through GitHub Secrets (`Settings -> Secrets and variables -> Actions -> Secrets`).

| Secret Name | Environment Scope | Description |
| :--- | :--- | :--- |
| `SMOKE_TEST_TOKEN` | staging, production | Synthetic test user Bearer token used by `scripts/release/smoke.py` to verify authenticated `/api/v1/me` and `/api/v1/feed` endpoints. Identifiers are scrubbed from workflow logs. |

## 3. GitHub Environments Setup

The repository defines two formal environments in GitHub repository settings:

1. **`staging`**:
   - Deployment branch: `main`
   - Protection rules: None (automated deployment triggered after CI completion on `main`).
2. **`production`**:
   - Deployment branch: `main`
   - Protection rules:
     - **Required reviewers**: Founder / Lead Architect approval required before any deployment step executes.
     - **Wait timer**: Optional 5-minute soak timer between approval and task execution.
