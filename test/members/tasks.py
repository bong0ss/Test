import logging
import time

from celery import shared_task
from celery_progress.backend import ProgressRecorder

from .utility import custom_data

logger = logging.getLogger(__name__)


@shared_task
def add(x, y):
    return x + y


@shared_task
def sub(x, y):
    return x - y


@shared_task
def mult(x, y):
    return x * y


@shared_task(name="members.tasks.timer", bind=True)
def timer(self, time_left):
    progress = ProgressRecorder(self)
    custom_data(
        data=f"Action started at {time.ctime()}, await {time_left} seconds! Predicted to finish at {time.ctime(time.time() + time_left)}"
    )
    for i in range(time_left):
        time.sleep(1)
        progress.set_progress(i + 1, time_left, description="Przetwarzanie...")
    custom_data(data=f"Action finished at {time.ctime()}")
    return "Finished!"
