FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/interview-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/interview-service .

EXPOSE 5003

CMD ["python", "app.py"]
