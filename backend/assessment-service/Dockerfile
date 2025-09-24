FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/assessment-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/assessment-service .

EXPOSE 5008

CMD ["python", "app.py"]
