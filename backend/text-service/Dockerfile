# SkillScreen Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies with explicit package versions for security
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9ubuntu3 \
    curl=7.81.0-1ubuntu1.14 \
    software-properties-common=0.99.22.9 \
    git=1:2.34.1-1ubuntu1.9 \
    libpq-dev=14.9-0ubuntu0.22.04.1 \
    libmagic1=5.41-3ubuntu0.1 \
    libmagic-dev=5.41-3ubuntu0.1 \
    ffmpeg=7:4.4.2-0ubuntu0.22.04.1 \
    libsndfile1=1.0.31-2ubuntu0.1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements_production.txt .
RUN pip install --no-cache-dir -r requirements_production.txt

# Copy only necessary application files (not recursive)
COPY fastapi_app.py .
COPY services/ ./services/
COPY utils/ ./utils/
COPY database/ ./database/
COPY schemas/ ./schemas/

# Create necessary directories
RUN mkdir -p logs uploads reports static

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
