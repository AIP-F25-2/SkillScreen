FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/common-service:/app/text-service

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install coding-service requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy coding-service code
COPY . .

# Note: text-service code will be mounted via docker-compose volumes
# This allows coding-service to import EnhancedLLMService from text-service
# The volumes in docker-compose.dev.yml mount:
# - ./backend/text-service:/app/text-service
# This mounts the entire text-service directory structure for proper imports

CMD ["uvicorn", "coding:app", "--host", "0.0.0.0", "--port", "8080"]