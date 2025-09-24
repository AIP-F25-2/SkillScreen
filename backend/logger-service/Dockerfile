FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/logger-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/logger-service .

EXPOSE 5010

CMD ["python", "app.py"]
