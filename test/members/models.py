from django.contrib.auth.models import User
from django.db import models

class Member(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    phone = models.IntegerField(null=True)
    joined_date = models.DateField(null=True)

class PcComp(models.Model):
    partname = models.CharField(max_length=255, null=False)
    producer = models.CharField(max_length=255, null=True)
    quantity = models.IntegerField(null=False)
    price = models.IntegerField(null=True)

class UserPermissions(User):
    class Meta:
        proxy = True
        permissions = [
            ("multiplication_access", "Can access multiplication"),
        ]