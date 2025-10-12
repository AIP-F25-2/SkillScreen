FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- System Dependencies ---
# Includes: cmake, OpenCV runtime libs, git (for model weights), and build essentials for compiling dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    cmake \
    libgl1 \
    libglib2.0-0 \
    git \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Python Dependencies ---
WORKDIR /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# --- Copy App Code ---
COPY . /app

# --- Environment Variables ---
# These make Ultralytics write config/settings to a persistent folder (mounted via Docker Compose)
ENV YOLO_CONFIG_DIR=/app/.ultra_cfg \
    YOLOv8_DIR=/app/.ultra_cfg

# --- Default Command ---
# If you’re using FastAPI (as most of your files suggest)
CMD ["/bin/sh", "-lc", "uvicorn app.video-service:app --host 0.0.0.0 --port ${SERVER_PORT:-5010}"]
