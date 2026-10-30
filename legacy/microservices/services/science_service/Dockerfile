FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 9002

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${SCIENCE_SERVICE_PORT:-9002}"]
