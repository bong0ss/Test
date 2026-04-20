import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test.settings")

if os.environ.get("REDIS_PASS"):
    broker_url = f"redis://:{os.environ.get("REDIS_PASS")}@{os.environ.get("REDIS_HOST")}:{os.environ.get("REDIS_PORT")}/0"
else:
    broker_url = (
        f"redis://{os.environ.get("REDIS_HOST")}:{os.environ.get("REDIS_PORT")}/0"
    )

app = Celery("members", broker=broker_url)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.update(
    result_expires=3600,
)

if __name__ == "__main__":
    app.start()
