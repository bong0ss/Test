from django.apps import AppConfig


class MembersConfig(AppConfig):
    name = "members"


class LoggingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "logging"

    def ready(self):
        import members.signals

        members.signals
