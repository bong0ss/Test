FROM python:3.14.4-alpine

WORKDIR /app

COPY requirements.txt .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/test:/app

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "cd /app/test && celery -A members flower"]
