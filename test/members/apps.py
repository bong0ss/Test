from django.apps import AppConfig


class MembersConfig(AppConfig):
    name = "members"


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "members"

    def ready(self):
        import members.signals

        members.signals
