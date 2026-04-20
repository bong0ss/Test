import logging
import time

from celery import shared_task

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


@shared_task(name="members.tasks.timer")
def timer(time_left):
    logger.info(f"Action started at {time.ctime()}, await {time_left} seconds!")
    time.sleep(time_left)
    logger.info(f"Action finished at {time.ctime()}")
    return "Finished!"
