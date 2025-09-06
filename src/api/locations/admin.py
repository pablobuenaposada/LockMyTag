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
        "latitude",
        "longitude",
        "timestamp",
        "google_maps_link",
    )
    list_filter = ["tag__name", "timestamp"]

    def google_maps_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.google_maps_url,
            obj.google_maps_url,
        )


admin.site.register(Tag, TagAdmin)
admin.site.register(TagLocation, TagLocationAdmin)
