# Stage 1: builder
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# Stage 2: runtime
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY backend/main.py backend/models.py backend/seed_data.py backend/achievement_engine.py ./
COPY backend/routers ./routers
COPY backend/scripts ./scripts

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]