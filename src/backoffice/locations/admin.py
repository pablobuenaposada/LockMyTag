from django.contrib import admin
from django.utils.html import format_html

from .models import Tag, TagLocation


class TagAdmin(admin.ModelAdmin):
    exclude = ("id",)
    readonly_fields = ("created", "modified")
    list_display = ("id", "name")


class TagLocationAdmin(admin.ModelAdmin):
    readonly_fields = ("created", "modified")
    list_display = (
        "id",
        "tag__name",
        "battery_badge",
        "latitude",
        "longitude",
        "timestamp",
        "google_maps_link",
    )
    list_filter = ["tag__name", "timestamp"]
    ordering = ["-timestamp"]

    def google_maps_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.google_maps_url,
            obj.google_maps_url,
        )

    def battery_badge(self, obj):
        color_by_level = {
            TagLocation.BatteryLevel.FULL: "#16a34a",
            TagLocation.BatteryLevel.MEDIUM: "#ca8a04",
            TagLocation.BatteryLevel.LOW: "#ea580c",
            TagLocation.BatteryLevel.VERY_LOW: "#dc2626",
        }
        label = obj.get_battery_display() if obj.battery else "None"
        color = color_by_level.get(obj.battery, "#6b7280")
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>', color, label
        )

    battery_badge.short_description = "battery"
    battery_badge.admin_order_field = "battery"


admin.site.register(Tag, TagAdmin)
admin.site.register(TagLocation, TagLocationAdmin)
