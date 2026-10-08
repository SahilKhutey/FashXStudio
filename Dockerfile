FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY schemas ./schemas
COPY database ./database
COPY alembic.ini ./alembic.ini

RUN pip install --no-cache-dir uv==0.12.13 \
    && uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "backend/fashx/main.py", "--host", "0.0.0.0", "--port", "8000"]
