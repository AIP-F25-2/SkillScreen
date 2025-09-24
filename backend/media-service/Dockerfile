FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/media-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/media-service .

EXPOSE 5004

CMD ["python", "app.py"]
