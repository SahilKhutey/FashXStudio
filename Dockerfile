# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build

WORKDIR /src
RUN pip install --no-cache-dir build wheel
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY database ./database
COPY schemas ./schemas
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim

# Create dedicated non-root user for principle of least privilege
RUN useradd --system --uid 10001 --no-create-home app

WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY alembic.ini ./
COPY database ./database

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && curl -fsSL \
    https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem \
    -o /etc/ssl/certs/aws-rds-global-bundle.pem \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV DB_SSL_CA_FILE=/etc/ssl/certs/aws-rds-global-bundle.pem

USER 10001
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/live')"

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "--timeout", "90", "--graceful-timeout", "30", "--forwarded-allow-ips", "*", "fashx.main:app"]
