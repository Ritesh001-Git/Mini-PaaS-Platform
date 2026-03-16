FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y git build-essential netcat-openbsd

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD bash -c "until nc -z db 5432; do echo waiting for postgres; sleep 2; done; uvicorn main:app --host 0.0.0.0 --port 8000"