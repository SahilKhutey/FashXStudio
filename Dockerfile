# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build

WORKDIR /src
RUN pip install --no-cache-dir build wheel
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY database ./database
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim

# Create dedicated non-root user for principle of least privilege
RUN useradd --system --uid 10001 --no-create-home app

WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY alembic.ini ./
COPY database ./database

USER 10001
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/system/health/live')"

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "--timeout", "30", "--graceful-timeout", "30", "--forwarded-allow-ips", "*", "fashx.main:app"]
