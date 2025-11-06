# syntax=docker/dockerfile:1.7
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn
COPY . /app
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app
USER appuser
# ENV SERVER_HOST=0.0.0.0 SERVER_PORT=8080 UPLOAD_FOLDER=/app/uploads MAX_CONTENT_LENGTH_BYTES=524288000 CORS_ORIGINS="*"
ENV SERVER_HOST=0.0.0.0 SERVER_PORT=8080 UPLOAD_FOLDER=/app/temp/uploads MAX_CONTENT_LENGTH_BYTES=524288000 CORS_ORIGINS="*"
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1
CMD sh -c 'exec gunicorn --workers ${GUNICORN_WORKERS:-3} --threads ${GUNICORN_THREADS:-2} --timeout ${GUNICORN_TIMEOUT:-120} --bind 0.0.0.0:${SERVER_PORT} media_service:app'
