FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/coding-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/coding-service .

EXPOSE 5009

CMD ["python", "app.py"]
