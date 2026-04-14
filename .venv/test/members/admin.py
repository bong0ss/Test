from django.contrib import admin
from .models import Member
from .models import PcComp

class MemberAdmin(admin.ModelAdmin):
    list_display = ("firstname", "lastname", "phone", "joined_date")

class PcComponents(admin.ModelAdmin):
    list_display = ("partname", "producer", "quantity", "price")

admin.site.register(Member, MemberAdmin)
admin.site.register(PcComp, PcComponents)