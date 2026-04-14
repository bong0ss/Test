from celery import Celery, shared_task

app = Celery("tasks", broker="")


@shared_task
def add(x, y):
    return x + y


@shared_task
def sub(x, y):
    return x - y
