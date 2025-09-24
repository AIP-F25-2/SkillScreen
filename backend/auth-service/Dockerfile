FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/auth-service .

EXPOSE 5002

CMD ["python", "app.py"]
