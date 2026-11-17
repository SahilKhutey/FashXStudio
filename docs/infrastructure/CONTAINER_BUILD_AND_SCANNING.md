# Container Build and Security Scanning Specification

## 1. Multi-Stage Dockerfile Architecture

The FashXStudio container image is produced from a multi-stage `Dockerfile` optimizing image size, build speed, and runtime attack surface reduction:

```dockerfile
# Stage 1: Build stage
FROM python:3.12-slim AS build
WORKDIR /src
RUN pip install --no-cache-dir build wheel
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY database ./database
COPY schemas ./schemas
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# Stage 2: Minimal runtime stage
FROM python:3.12-slim
RUN useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY alembic.ini ./
COPY database ./database

# Install AWS RDS CA certificate bundle
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && curl -fsSL https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o /etc/ssl/certs/aws-rds-global-bundle.pem \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

USER 10001
EXPOSE 8000
```

### Security Hardening Measures:
- **Non-Root User**: The container executes as UID `10001` (`app`), preventing container breakout or unauthorized host filesystem tampering.
- **Minimal Dependencies**: Build tools, compilers, and wheel caches are stripped from the final runtime image.
- **Explicit Exclusions**: `.dockerignore` blocks test artifacts, evaluation datasets, git history, and local `.env` files from ever entering the image layers.

## 2. Container Vulnerability Scanning with Trivy

Before any container image is deployed to staging or promoted to production, it undergoes an automated static security vulnerability scan via Aqua Security Trivy:

```yaml
- name: Image Vulnerability Scan (Trivy)
  uses: aquasecurity/trivy-action@v0.28.0
  with:
    image-ref: ${{ steps.build-push.outputs.image_uri }}
    format: "table"
    exit-code: "1"
    ignore-unfixed: true
    severity: "HIGH,CRITICAL"
```

### Gate Rules:
- Any `CRITICAL` or `HIGH` Common Vulnerabilities and Exposures (CVE) that has a vendor-provided fix will cause the step to exit with code `1`, halting deployment.
- Scans are recorded in GitHub Actions workflow logs.
