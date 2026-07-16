# =====================================================================
# Dockerfile — Analytics Service (FastAPI + SQLAlchemy + Qdrant + Kafka)
# =====================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    librdkafka-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi --only main

# --- Final Production Stage ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Install native librdkafka (confluent-kafka needs it at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app source code and shared domain libraries
COPY apps/analytics-service/src/ /app/apps/analytics-service/src/
COPY packages/ /app/packages/

# Set Python execution paths
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

ENTRYPOINT ["uvicorn", "apps.analytics-service.src.main:app", "--host", "0.0.0.0", "--port", "8001"]
