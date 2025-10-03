FROM python:3.12-slim

# Install ffmpeg and other dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use .env variables inside container
ENV FLASK_APP=app.py

CMD ["python", "app.py"]
