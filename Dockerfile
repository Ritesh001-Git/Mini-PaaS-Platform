FROM python:3.10

WORKDIR /app

# 1️⃣ Copy requirements first
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 2️⃣ Copy backend code
COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]