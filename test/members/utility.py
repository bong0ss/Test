from .signals import custom_data_signal, custom_signal


def send_data(request):
    custom_signal.send(
        sender=None, user=request.user, information=(request, request.GET, request.POST)
    )


def custom_data(data):
    custom_data_signal.send(sender=None, information=(data))
