# syntax=docker/dockerfile:1.7

# ---- Base image ----
FROM python:3.11-slim

# ---- Environment setup ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ---- System dependencies + user creation ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg && \
    useradd -m -u 10001 appuser && \
    rm -rf /var/lib/apt/lists/*

# ---- App setup ----
WORKDIR /app

# Copy dependency list separately for better caching
COPY requirements.txt .

# ---- Install dependencies ----
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# ---- Copy application code ----
# NOTE: Sensitive files (.env, .git, build artifacts) are excluded via .dockerignore
COPY app /app
COPY media_service.py /app/

# ---- File permissions & uploads dir ----
RUN mkdir -p /app/uploads && \
    chown -R appuser:appuser /app

USER appuser

# ---- Environment variables ----
ENV SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8080 \
    UPLOAD_FOLDER=/app/temp/uploads \
    MAX_CONTENT_LENGTH_BYTES=524288000 \
    CORS_ORIGINS="*"

# ---- Expose port ----
EXPOSE 8080

# ---- Health check ----
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["curl", "-fsS", "http://127.0.0.1:8080/healthz"]

# ---- Start Gunicorn ----
CMD ["/bin/sh", "-c", "exec gunicorn \
    --workers ${GUNICORN_WORKERS:-3} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --bind 0.0.0.0:${SERVER_PORT} \
    media_service:app"]
