import logging

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import Signal, receiver

logger = logging.getLogger(__name__)
custom_signal = Signal()
custom_data_signal = Signal()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info(
        f"User {user.username} logged in from {request.META.get('REMOTE_ADDR')}"
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    logger.info(f"User {user.username} just logged out")


@receiver(user_login_failed)
def log_user_failed(sender, credentials, request, **kwargs):
    logger.warning(f"User failed to login {credentials.get('username')}")


@receiver(custom_signal)
def log_req_finished(sender, **kwargs):
    user = kwargs.get("user")
    information = kwargs.get("information")
    logger.info(f"User {user} | Action: {information}")


@receiver(custom_data_signal)
def log_custom_data(sender, **kwargs):
    data = kwargs.get("information")
    logger.info(data)
