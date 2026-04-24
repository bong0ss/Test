from django.contrib import admin

from .models import Tools


class Admin(admin.ModelAdmin):
    list_display = ("tool_id", "name", "description", "inputs", "outputs")


admin.site.register(Tools, Admin)
