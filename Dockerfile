FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    LUMINA_ENV=production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin lumina

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend

RUN mkdir -p /app/backend/data/vector_store /app/backend/data/logs \
    && chown -R lumina:lumina /app

USER lumina

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=25s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/health >/dev/null || exit 1

# Do not trust arbitrary X-Forwarded-For. Set LUMINA_TRUST_PROXY=true only
# behind a reverse proxy that overwrites the client IP header.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
