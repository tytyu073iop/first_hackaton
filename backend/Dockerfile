# Stage 1: builder
FROM python:3.11.15-trixie AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# Stage 2: runtime
FROM python:3.11.15-trixie

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY backend/main.py backend/models.py backend/seed_data.py backend/achievement_engine.py backend/partners_osm.json ./
COPY backend/routers ./routers
COPY backend/scripts ./scripts

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "main.py"]