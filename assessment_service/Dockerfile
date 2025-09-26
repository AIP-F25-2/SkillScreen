FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY assessment_service/ .

CMD ["uvicorn", "assessment:app", "--host", "0.0.0.0", "--port", "8002"]