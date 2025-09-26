FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY coding_service/ .

CMD ["uvicorn", "coding:app", "--host", "0.0.0.0", "--port", "8003"]