from django.contrib import admin

from .models import Lock


class LockAdmin(admin.ModelAdmin):
    list_display = ("id", "tag", "status", "last_notified")
    readonly_fields = ("last_notified", "created", "modified")
    list_filter = ["tag__name"]


admin.site.register(Lock, LockAdmin)
