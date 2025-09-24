FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/audio-ai-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/audio-ai-service .

EXPOSE 5006

CMD ["python", "app.py"]
