from django.contrib import admin
from django.utils.html import format_html

from .models import Lock


class LockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tag__name",
        "colored_status",
        "radius",
        "schedule_day",
        "schedule_start_time",
        "schedule_end_time",
    )
    readonly_fields = ("created", "modified")
    list_filter = ["tag__name"]

    def colored_status(self, obj):
        color = "green" if obj.status == "active" else "red"
        return format_html('<span style="color: {};">{}</span>', color, obj.status)

    colored_status.admin_order_field = "status"
    colored_status.short_description = "Status"


admin.site.register(Lock, LockAdmin)
