FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/api-gateway .

EXPOSE 5000

CMD ["python", "app.py"]
