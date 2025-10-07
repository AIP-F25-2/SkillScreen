FROM python:3.10-slim

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# ---- Install shared requirements ----
COPY ../../requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# ---- Install service-specific requirements ----
COPY ./requirements.txt /service-requirements.txt
RUN pip install --no-cache-dir -r /service-requirements.txt

COPY . /app

CMD ["sh", "-c", "uvicorn user:app --host 0.0.0.0 --port ${PORT:-8080}"]