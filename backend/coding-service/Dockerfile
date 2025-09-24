FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI for code execution
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5009

CMD ["python", "app.py"]
