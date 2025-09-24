FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/notification-service .

EXPOSE 5011

CMD ["python", "app.py"]
