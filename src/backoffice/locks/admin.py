from django.contrib import admin

from .models import Lock


class LockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tag__name",
        "status",
        "radius",
        "schedule_day",
        "schedule_start_time",
        "schedule_end_time",
    )
    readonly_fields = ("created", "modified")
    list_filter = ["tag__name"]


admin.site.register(Lock, LockAdmin)
