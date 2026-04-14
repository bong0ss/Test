from .signals import custom_signal


def send_data(request):
    custom_signal.send(
        sender=None, user=request.user, information=(request, request.GET, request.POST)
    )
