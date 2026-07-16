# =====================================================
# Dockerfile — Camera Service (FastAPI + RTSP Health check)
# =====================================================

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi --only main

# --- Runner Production Stage ---
FROM python:3.11-slim AS runner

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY apps/camera-service/src/ /app/apps/camera-service/src/
COPY packages/ /app/packages/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8002

ENTRYPOINT ["uvicorn", "apps.camera-service.src.main:app", "--host", "0.0.0.0", "--port", "8002"]
