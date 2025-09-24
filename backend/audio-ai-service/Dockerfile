FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5006

CMD ["python", "app.py"]
