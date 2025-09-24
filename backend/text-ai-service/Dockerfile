FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/text-ai-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/text-ai-service .

EXPOSE 5007

CMD ["python", "app.py"]
