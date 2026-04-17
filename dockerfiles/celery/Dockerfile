FROM python:3.14.4-alpine

WORKDIR /app

COPY requirements.txt .

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["celery", "-A", "members", "worker", "-l", "INFO"]