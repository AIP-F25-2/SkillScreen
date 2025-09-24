FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/video-ai-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/video-ai-service .

EXPOSE 5005

CMD ["python", "app.py"]
