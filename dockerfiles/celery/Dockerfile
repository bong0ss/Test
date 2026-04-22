FROM python:3.14-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/test:/app

EXPOSE 8000

CMD ["sh", "-c", "cd /app/test && celery -A members worker -l INFO -E"]
