from django.contrib.auth.models import User
from django.db import models


class Tools(models.Model):
    tool_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    inputs = models.CharField(max_length=255)
    outputs = models.CharField(max_length=255)


class UserPermissions(User):
    class Meta:
        proxy = True
        permissions = [
            ("multiplication_access", "Can access multiplication"),
        ]
