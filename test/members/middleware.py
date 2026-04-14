import logging

logger = logging.getLogger(__name__)


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_respone = self.get_respone

    def __call__(self, request):
        if request.user.is_authenticated:
            user = request.user
        else:
            user = "Anonymous"

        path = request.path
        method = request.method
        if request.methode == "POST":
            data = request.POST.dict()
        else:
            data = ""

        logger.info(f"User: {user} | Method: {method} | Path: {path} | Data: {data}")

        return self.get_respone
