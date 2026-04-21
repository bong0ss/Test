FROM python:3.14-alpine

RUN apk add --no-cache su-exec

RUN addgroup -g 1000 appuser && \
    adduser -u 1000 -G appuser -D -s /bin/sh appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER root
RUN chown -R appuser:appuser /app

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/test:/app

EXPOSE 8000

CMD ["sh", "-c", "cd /app/test && celery -A members worker -l INFO -E"]
