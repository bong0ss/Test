from django.contrib.auth.models import User
from django.db import models  # noqa: F401


class UserPermissions(User):
    class Meta:
        proxy = True
        permissions = [
            ("multiplication_access", "Can access multiplication"),
        ]
