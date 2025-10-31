# SkillScreen Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    software-properties-common \
    git \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_production.txt .
RUN pip install --no-cache-dir -r requirements_production.txt

# Copy only necessary application code
COPY fastapi_app.py simple_fastapi_app.py ./
COPY services ./services
COPY utils ./utils
COPY database ./database
COPY schemas ./schemas
COPY README_PRODUCTION.md CONFIG_SETUP.md DEPLOYMENT_SECURITY.md ./

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
