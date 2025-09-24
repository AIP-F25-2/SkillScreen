FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/user-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/user-service .

EXPOSE 5001

CMD ["python", "app.py"]
